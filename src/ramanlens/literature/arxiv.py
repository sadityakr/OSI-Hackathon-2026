"""Fetch arXiv PDFs into the local cache.

Bond returns arXiv ids (``2211.12939v1``); this module turns them into a PDF on disk under
``data/raw/pdfs/<bare_id>.pdf``. Only arXiv is supported in the hackathon build; PubMed-only
papers are cited without figures.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import httpx

from ..tracing import traced

_VERSION_RE = re.compile(r"v\d+$")
_USER_AGENT = "ramanlens/0.0.1 (research prototype)"


def bare_id(arxiv_id: str) -> str:
    """``2211.12939v1`` -> ``2211.12939``; ``arXiv:2211.12939`` -> ``2211.12939``."""
    s = arxiv_id.strip()
    s = re.sub(r"^arxiv:\s*", "", s, flags=re.IGNORECASE)
    return _VERSION_RE.sub("", s)


@traced("figure.fetch")
def fetch_pdf(arxiv_id: str, cache_dir, *, timeout: float = 60.0, force: bool = False) -> Optional[Path]:
    """Download ``https://arxiv.org/pdf/<id>`` into ``cache_dir`` and return the path, or None.

    Returns the cached file without a network call when it exists. Verifies the ``%PDF`` magic
    bytes so an HTML error page is never stored as a PDF.
    """
    bid = bare_id(arxiv_id)
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    out = cache_dir / f"{bid}.pdf"
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
