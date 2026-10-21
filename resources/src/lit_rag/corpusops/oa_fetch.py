"""Open-access PDF fallback: fetch a paper's PDF by DOI/arXiv id when Zotero has none attached.

A Zotero item with no PDF child is a dead end for the corpus otherwise — no PDF means no parse, no
embedding, nothing to retrieve. This is the same problem the lit skill's four-step pipeline solves
for the Obsidian vault (grab inbox -> Unpaywall -> auto-grab publisher -> tag needs-PDF), but only
its OA-lookup step is portable to a headless server: the auto-grab step drives a real, logged-in
Chrome over CDP, which needs an interactive desktop and a warmed browser profile. This module keeps
only the two plain-HTTP legs — Unpaywall and direct arXiv download — that work the same on a laptop
or the JGU VM.

Input:
    A DOI or arXiv id, and (Unpaywall only) a contact email for its polite pool (reuses
    CROSSREF_MAILTO — same etiquette requirement as the CrossRef calls already made elsewhere).
Process:
    Unpaywall: GET /v2/{doi} -> best_oa_location.url_for_pdf, then download and verify the %PDF
    magic bytes. arXiv: GET arxiv.org/pdf/{id} directly (arXiv PDFs are always OA).
Output:
    Raw PDF bytes, or None if no open-access copy exists (abstain — never fabricate a "found" PDF
    from a landing page or an HTML response).
"""

from __future__ import annotations

import re

import httpx

ARXIV_DOI_RE = re.compile(r"10\.48550/arxiv\.(.+)", re.IGNORECASE)
ARXIV_EXTRA_RE = re.compile(r"arxiv:\s*([\w.-]+)", re.IGNORECASE)


def arxiv_id_from_item(doi: str | None, extra: str | None) -> str | None:
    """Best-effort arXiv id from a Zotero item's DOI (arXiv's own DOI prefix) or its ``extra`` field."""
    if doi:
        m = ARXIV_DOI_RE.match(doi.strip())
        if m:
            return m.group(1)
    if extra:
        m = ARXIV_EXTRA_RE.search(extra)
        if m:
            return m.group(1)
    return None


def _download_pdf(url: str, *, mailto: str | None = None, timeout: float = 60.0) -> bytes | None:
    headers = {"User-Agent": f"lit-rag/0.1 (mailto:{mailto})" if mailto else "lit-rag/0.1"}
    try:
        r = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
    except httpx.HTTPError:
        return None
    if r.status_code != 200 or not r.content.startswith(b"%PDF"):
        return None
    return r.content


def unpaywall_pdf(doi: str, *, mailto: str, timeout: float = 30.0) -> bytes | None:
    """Open-access PDF for ``doi`` via Unpaywall, or None if no location actually yields one.

    Tries every location Unpaywall lists (best first), not just ``best_oa_location``: publisher
    links are routinely 403-blocked for a scripted client even when genuinely open access, while a
    repository/institutional mirror of the same paper usually isn't. One failed location must not
    give up on the others — a paper Unpaywall calls OA is exactly the case where a fallback is worth
    trying harder, not abstaining early.
    """
    try:
        r = httpx.get(f"https://api.unpaywall.org/v2/{doi}", params={"email": mailto}, timeout=timeout)
    except httpx.HTTPError:
        return None
    if r.status_code != 200:
        return None
    data = r.json()
    locations = [data["best_oa_location"]] if data.get("best_oa_location") else []
    locations += [loc for loc in data.get("oa_locations") or [] if loc not in locations]
    for loc in locations:
        for url in (loc.get("url_for_pdf"), loc.get("url")):
            if not url:
                continue
            pdf = _download_pdf(url, mailto=mailto, timeout=timeout)
            if pdf:
                return pdf
    return None


def arxiv_pdf(arxiv_id: str, *, mailto: str | None = None, timeout: float = 60.0) -> bytes | None:
    """PDF bytes for an arXiv id, straight from arxiv.org (always open access)."""
    bare = re.sub(r"v\d+$", "", arxiv_id.strip())  # a version suffix still resolves, but normalize
    return _download_pdf(f"https://arxiv.org/pdf/{bare}", mailto=mailto, timeout=timeout)
