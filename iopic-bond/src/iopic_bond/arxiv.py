"""Fetch arXiv PDFs.

Bond returns arXiv ids (``2211.12939v1``); this module downloads ``https://arxiv.org/pdf/<id>`` to a
path the store chooses (``papers/<base_id>/paper.pdf``). Only arXiv is supported; PubMed-only papers
are cited without figures.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import httpx

from . import __version__
from .tracing import traced

_VERSION_RE = re.compile(r"v\d+$")
_USER_AGENT = f"iopic-bond/{__version__} (research prototype)"


def bare_id(arxiv_id: str) -> str:
    """``2211.12939v1`` -> ``2211.12939``; ``arXiv:2211.12939`` -> ``2211.12939``."""
    s = arxiv_id.strip()
    s = re.sub(r"^arxiv:\s*", "", s, flags=re.IGNORECASE)
    return _VERSION_RE.sub("", s)


def looks_like_arxiv_id(s: str) -> bool:
    """New-style (``2211.12939``) or old-style (``cond-mat/0501234``) arXiv id, version optional."""
    b = bare_id(s)
    return bool(re.fullmatch(r"\d{4}\.\d{4,5}", b) or re.fullmatch(r"[a-z\-]+(\.[A-Z]{2})?/\d{7}", b))


@traced("figure.fetch")
def fetch_pdf(arxiv_id: str, out_path, *, timeout: float = 60.0, force: bool = False) -> Optional[Path]:
    """Download the PDF to ``out_path`` and return it, or None on failure.

    Returns the existing file without a network call unless ``force``. Verifies the ``%PDF`` magic
    bytes so an HTML error page is never stored as a PDF.
    """
    bid = bare_id(arxiv_id)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and not force:
        return out
    try:
        r = httpx.get(f"https://arxiv.org/pdf/{bid}", headers={"User-Agent": _USER_AGENT},
                      timeout=timeout, follow_redirects=True)
    except httpx.HTTPError:
        return None
    if r.status_code != 200 or not r.content.startswith(b"%PDF"):
        return None
    out.write_bytes(r.content)
    return out
