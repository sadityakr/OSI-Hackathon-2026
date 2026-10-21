"""External bibliographic lookup via OpenAlex — the open world around our closed corpus.

The corpus is a **closed set embedded in an open one**: 226 of 5,401 catalog entities are papers we
actually hold, so ~90% of a citation hop lands on a work whose *identity* we know (a DOI, from ADR-0003
/ ADR-0005) but whose text we do not. ``availability`` (see :mod:`tools`) tells the agent that up front;
this module is what it does next — fetch the missing work's bibliographic identity **and abstract** live
from OpenAlex, instead of us backfilling abstracts into the store.

Three commitments, all of them the project's spine rather than HTTP detail:

* **Provenance is explicit.** Every result carries ``source = "openalex"`` (top level *and* inside
  ``work``, since agents pass the inner dict around). An external abstract is a *different epistemic
  object* from a passage in our own index: it is a publisher-supplied summary we did not parse, cannot
  page-locate, and must never let a claim be attributed to as if it were a held passage.
* **Structured abstention (ADR-0009).** Every call returns a ``status`` from the CLOSED vocabulary in
  :data:`OPENALEX_STATUSES` — a timeout, a DNS failure or a malformed body is ``upstream_error`` **as
  data**, never a raised exception. ``no_abstract`` is a *common, expected, non-error* outcome (OpenAlex
  had an abstract for ~57% of a sample of the 40 most-cited unheld DOIs) and still returns the
  bibliographic identity.
* **Read-only, no state.** Nothing here touches the database; the serving DB stays read-only from the
  agent's side (ADR-0009 §3).

The one real gotcha is the **abstract**: OpenAlex ships it as an ``abstract_inverted_index``
(``{token: [positions]}``), not prose, so it must be reconstructed — :func:`reconstruct_abstract`, a
pure function, offline-tested. Everything shaping-related is pure; only :func:`fetch_work` touches the
network, and it takes an injectable ``http_get`` seam so the offline gate never makes a request.

**No caching in v1** (deliberately out of scope — see ``docs/issues/0019``). **No mailto/"polite pool"
parameter** and no email in the User-Agent: this is a privacy-preserving project and the identifier we
send is the tool, not a person.
"""

from __future__ import annotations

from urllib.parse import quote

import httpx

# The provider identity stamped on every result — provenance, not decoration (see module docstring).
SOURCE_OPENALEX = "openalex"

OPENALEX_WORKS_URL = "https://api.openalex.org/works/doi:"
# Descriptive but ANONYMOUS: no mailto, no address, in the UA, the URL, or any header.
USER_AGENT = "lit-RAG/0.1 (research prototype)"
DEFAULT_TIMEOUT = 10.0

# The CLOSED status vocabulary for external lookup — the same abstention contract the store tools
# honour (ADR-0009), scoped to an upstream HTTP source. Adding a value is a CONTRACT CHANGE for every
# client: route it through this block, never an inline literal.
OA_OK = "ok"
OA_NOT_FOUND = "not_found"  # OpenAlex has no work for this DOI
OA_NO_ABSTRACT = "no_abstract"  # work found, identity returned, but no abstract upstream (~43%)
OA_UPSTREAM_ERROR = (
    "upstream_error"  # network/timeout/5xx/malformed body — data, never an exception
)
OA_BAD_REQUEST = "bad_request"  # not a DOI we can even ask about
OPENALEX_STATUSES = frozenset(
    {OA_OK, OA_NOT_FOUND, OA_NO_ABSTRACT, OA_UPSTREAM_ERROR, OA_BAD_REQUEST}
)


# ── pure shaping (offline-tested; no network) ───────────────────────────────────────────────────────


def normalize_doi(raw: str | None) -> str | None:
    """Reduce any DOI spelling to the bare, lowercase form the catalog stores (``10.1103/revmod…``).

    Accepts the resolver URL (``https://doi.org/…``, ``http://dx.doi.org/…``) and the ``doi:`` prefix.
    Returns ``None`` when the input is not recognisably a DOI — the caller then abstains with
    ``bad_request`` rather than sending a guess upstream.
    """
    if not raw:
        return None
    s = raw.strip()
    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
    ):
        if s.lower().startswith(prefix):
            s = s[len(prefix) :]
            break
    if s.lower().startswith("doi:"):
        s = s[4:]
    s = s.strip().lower()
    return s if s.startswith("10.") and "/" in s else None


def reconstruct_abstract(inverted_index: dict | None) -> str | None:
    """Rebuild prose from OpenAlex's ``abstract_inverted_index`` (``{token: [positions]}``).

    OpenAlex publishes abstracts as an inverted index rather than text. Each token maps to every
    position it occupies, so the abstract is recovered by scattering tokens into a position-indexed
    array and joining. Robust to the two things the payload does not promise: positions are neither
    sorted nor gap-free (a hole is simply dropped, never rendered as a blank), and a token may repeat.
    Returns ``None`` for a missing/empty index — that is the ``no_abstract`` case, not an error.
    """
    if not inverted_index:
        return None
    positions: dict[int, str] = {}
    for token, idxs in inverted_index.items():
        for i in idxs or []:
            if isinstance(i, int) and i >= 0:
                positions[i] = token
    if not positions:
        return None
    text = " ".join(positions[i] for i in sorted(positions))
    return text or None


def _authors(payload: dict) -> list[str]:
    """Ordered author display names from ``authorships`` (OpenAlex preserves author order)."""
    out = []
    for a in payload.get("authorships") or []:
        name = ((a or {}).get("author") or {}).get("display_name")
        if name:
            out.append(name)
    return out


def _venue(payload: dict) -> str | None:
    """The journal/venue name from ``primary_location.source`` (None for e.g. a bare preprint)."""
    src = (payload.get("primary_location") or {}).get("source") or {}
    return src.get("display_name")


def present_work(payload: dict, *, doi: str | None = None) -> dict:
    """Shape an OpenAlex ``work`` payload into the agent-facing dict — pure, no network.

    Only the fields an agent can act on: identity (title/authors/year/venue), the reconstructed
    abstract, an importance signal (``cited_by_count``), and two handles — ``doi_url`` and ``pdf_url``
    (from ``open_access.oa_url``; OpenAlex does not guarantee it is a direct PDF rather than a landing
    page, so treat it as a *handle*, exactly like ``pdf_path`` in :mod:`tools`). ``source`` rides
    *inside* the dict too, so the provenance survives being passed around on its own.
    """
    oa = payload.get("open_access") or {}
    resolved = normalize_doi(payload.get("doi")) or doi
    return {
        "source": SOURCE_OPENALEX,
        "doi": resolved,
        "doi_url": f"https://doi.org/{resolved}" if resolved else None,
        "openalex_id": payload.get("id"),
        "title": payload.get("title") or payload.get("display_name"),
        "authors": _authors(payload),
        "year": payload.get("publication_year"),
        "published_date": payload.get("publication_date"),
        "venue": _venue(payload),
        "type": payload.get("type"),
        "abstract": reconstruct_abstract(payload.get("abstract_inverted_index")),
        "cited_by_count": payload.get("cited_by_count"),
        "is_oa": oa.get("is_oa"),
        "pdf_url": oa.get("oa_url"),
    }


# ── the one networked function ──────────────────────────────────────────────────────────────────────


def fetch_work(doi: str, *, timeout: float = DEFAULT_TIMEOUT, http_get=None) -> dict:
    """Look one DOI up in OpenAlex and return ``{status, source, doi, work?, error?}``.

    Never raises: every failure mode — bad DOI, unknown work, timeout, 5xx, unparseable body — comes
    back as a ``status`` from :data:`OPENALEX_STATUSES`. ``http_get`` is a dependency-injection seam
    (defaults to ``httpx.get``) so the pure shaping can be exercised offline with a fake transport,
    keeping the network strictly outside ``make check`` — the Issue 0013 seam discipline applied to an
    upstream service instead of SQL.
    """
    key = normalize_doi(doi)
    if key is None:
        return {
            "status": OA_BAD_REQUEST,
            "source": SOURCE_OPENALEX,
            "doi": doi,
            "error": "not a recognisable DOI",
        }
    get = http_get or httpx.get
    url = OPENALEX_WORKS_URL + quote(key, safe="/:")
    try:
        resp = get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        if resp.status_code == 404:
            return {"status": OA_NOT_FOUND, "source": SOURCE_OPENALEX, "doi": key}
        if resp.status_code != 200:
            return {
                "status": OA_UPSTREAM_ERROR,
                "source": SOURCE_OPENALEX,
                "doi": key,
                "error": f"HTTP {resp.status_code}",
            }
        payload = resp.json()
    except Exception as e:  # noqa: BLE001 — abstention contract: upstream failure is DATA, not a raise
        return {
            "status": OA_UPSTREAM_ERROR,
            "source": SOURCE_OPENALEX,
            "doi": key,
            "error": f"{type(e).__name__}: {e}",
        }
    if not isinstance(payload, dict) or not payload.get("id"):
        return {
            "status": OA_UPSTREAM_ERROR,
            "source": SOURCE_OPENALEX,
            "doi": key,
            "error": "unexpected response body",
        }
    work = present_work(payload, doi=key)
    return {
        "status": OA_OK if work["abstract"] else OA_NO_ABSTRACT,
        "source": SOURCE_OPENALEX,
        "doi": key,
        "work": work,
    }
