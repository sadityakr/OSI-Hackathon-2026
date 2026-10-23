"""Talk to arXiv: normalise ids, read metadata from the export API, download PDFs politely.

Uses only the standard library (urllib), which honours HTTPS_PROXY / HTTP_PROXY on every OS.
arXiv's API terms (https://info.arxiv.org/help/api/tou.html) allow at most one request every
three seconds, one connection at a time, across all your machines. The wait is kept in a small
file in the library so that the MCP server and the command-line tool, running as separate
processes, share it. LITPICK_CONTACT adds your email to the User-Agent as a courtesy.
"""
from __future__ import annotations

import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from . import __version__
from .paths import library_home

API = "https://export.arxiv.org/api/query"
PDF = "https://arxiv.org/pdf/{id}"
MIN_GAP_S = 3.0
TIMEOUT_S = 60
ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

# New style 2407.13230 or 2407.13230v2; old style cond-mat/0601001v1 or math.GT/0309136
_NEW = re.compile(r"(?P<base>\d{4}\.\d{4,5})(?P<ver>v\d+)?")
_OLD = re.compile(r"(?P<base>[a-z\-]+(?:\.[A-Z]{2})?/\d{7})(?P<ver>v\d+)?")


class ArxivError(RuntimeError):
    pass


@dataclass
class ArxivId:
    base: str
    version: str | None = None  # "v2", or None for "latest"

    @property
    def full(self) -> str:
        return self.base + (self.version or "")


@dataclass
class Meta:
    base: str
    version: str
    title: str
    authors: list[str] = field(default_factory=list)
    published: str = ""  # YYYY-MM-DD of v1
    updated: str = ""
    abstract: str = ""

    @property
    def full(self) -> str:
        return self.base + self.version

    @property
    def year(self) -> int | None:
        return int(self.published[:4]) if self.published[:4].isdigit() else None


def parse_id(text: str) -> ArxivId | None:
    """Accept '2407.13230', 'arXiv:2407.13230v2', abs/pdf/html URLs, or old-style ids."""
    t = text.strip()
    t = re.sub(r"^(arxiv:)", "", t, flags=re.I)
    if "arxiv.org" in t:
        path = urllib.parse.urlparse(t if "://" in t else "https://" + t).path
        t = re.sub(r"^/(abs|pdf|html|e-print)/", "", path).removesuffix(".pdf").strip("/")
    for rx in (_NEW, _OLD):
        m = rx.fullmatch(t)
        if m:
            return ArxivId(m["base"], m["ver"])
    return None


def _user_agent() -> str:
    contact = os.environ.get("LITPICK_CONTACT", "").strip()
    tail = f"; mailto:{contact}" if contact else ""
    return f"litpick/{__version__} (personal research library{tail})"


def _wait_turn() -> None:
    stamp = library_home() / ".arxiv-last-request"
    try:
        last = float(stamp.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        last = 0.0
    gap = time.time() - last
    if gap < MIN_GAP_S:
        time.sleep(MIN_GAP_S - gap)
    try:
        stamp.write_text(str(time.time()), encoding="utf-8")
    except OSError:
        pass


def _get(url: str, retries: int = 3) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": _user_agent()})
    delay = 5.0
    for attempt in range(retries + 1):
        _wait_turn()
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                retry_after = e.headers.get("Retry-After", "")
                time.sleep(float(retry_after) if retry_after.isdigit() else delay)
                delay *= 2
                continue
            raise ArxivError(f"arXiv returned HTTP {e.code} for {url}") from e
        except urllib.error.URLError as e:
            if attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise ArxivError(f"could not reach arXiv ({e.reason}). Check the network or proxy.") from e
    raise ArxivError(f"giving up on {url}")


def fetch_meta(aid: ArxivId) -> Meta:
    """Metadata from the export API. Without a version, it reports the latest one."""
    url = API + "?" + urllib.parse.urlencode({"id_list": aid.full, "max_results": 1})
    root = ET.fromstring(_get(url))
    entry = root.find("a:entry", ATOM)
    if entry is None or entry.find("a:title", ATOM) is None:
        raise ArxivError(f"arXiv has no paper {aid.full}")
    abs_url = entry.findtext("a:id", default="", namespaces=ATOM)
    if "/api/errors" in abs_url:  # a malformed id comes back as an 'Error' entry, not an HTTP error
        raise ArxivError(f"arXiv rejected the id {aid.full}: "
                         + (entry.findtext("a:summary", default="", namespaces=ATOM) or "").strip())
    m = re.search(r"(v\d+)$", abs_url)
    version = aid.version or (m.group(1) if m else "v1")

    def clean(s: str | None) -> str:
        return re.sub(r"\s+", " ", s or "").strip()

    return Meta(
        base=aid.base,
        version=version,
        title=clean(entry.findtext("a:title", namespaces=ATOM)),
        authors=[clean(a.findtext("a:name", namespaces=ATOM)) for a in entry.findall("a:author", ATOM)],
        published=clean(entry.findtext("a:published", namespaces=ATOM))[:10],
        updated=clean(entry.findtext("a:updated", namespaces=ATOM))[:10],
        abstract=clean(entry.findtext("a:summary", namespaces=ATOM)),
    )


def download_pdf(full_id: str, dest: Path) -> Path:
    data = _get(PDF.format(id=full_id))
    if not data.startswith(b"%PDF"):
        raise ArxivError(f"arXiv did not return a PDF for {full_id} (withdrawn, or no PDF yet?)")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    tmp.write_bytes(data)
    tmp.replace(dest)  # atomic on every OS, so a crash never leaves half a PDF in the library
    return dest
