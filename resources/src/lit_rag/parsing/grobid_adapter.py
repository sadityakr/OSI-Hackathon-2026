"""Bibliographic adapter (ADR-0003, M6) — GROBID + CrossRef → identity, references, ``cites`` edges.

The *inter-document* half of the parsing layer. Docling (ADR-0002) builds structure and *intra*-document
edges but does no bibliography; GROBID parses the header (the paper's own identity) and the reference
list into structured records, and CrossRef resolves each reference string to a canonical **DOI** — the
durable join key that turns a ``cites`` edge from a dead end into a live cross-document link (design §4).

This module feeds the *same* ``BlockNode`` contract: it enriches a tree Docling already built rather than
owning structure. It is split, like the rest of the parser, into **pure logic** (TEI → records, CrossRef
JSON → match — unit-tested offline) and **thin I/O clients** (the GROBID HTTP service, the CrossRef REST
API — exercised only in live/manual runs, never in ``make check``).

Two stances inherited from the design:

* **Abstain over fabricate**, applied to metadata (ADR-0003 §2): a CrossRef match below the score gate
  leaves the DOI *unresolved* — never a low-confidence DOI asserted.
* **Citation count is catalog-only.** ``published_date`` and ``doi`` are immutable, intrinsic facts → they
  go on the tree. The citation count is a *drifting* snapshot (CrossRef ``is-referenced-by-count``) → it
  must NOT be serialized into ``tree.json`` (it would silently go stale); it is carried on attrs only long
  enough to project into the catalog, then stripped by :func:`strip_catalog_only` before the tree is
  written. Held with its **as-of** fetch date (design §3.7).

Citation linking is **uniform**: by the time this runs, :mod:`citation_normalize` (a parse-time stage)
has rewritten every citation style — superscript ``³⁴`` included — into the canonical ``[34]`` form in
the tree. So :func:`link_bracket_citations` scans one marker shape (``[N]`` / ``[N,M]`` / ``[N-M]``),
expands ranges/lists, and links each number to its reference by **bibliography order**
(ref *k* = ``<root>/ref{k}``), gated ``1 ≤ k ≤ n_refs`` (precision over recall). The two-stream
char-span reconciliation (design §5) is thus sidestepped for numbered styles; author–year remains open.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .schema import BlockNode, Edge

_TEI_NS = {"t": "http://www.tei-c.org/ns/1.0"}

# attrs that are CATALOG-ONLY (drifting) and must be stripped before writing tree.json (design §3.7)
CATALOG_ONLY_ATTRS = frozenset({"citation_count", "citation_count_as_of"})


# ── data records ────────────────────────────────────────────────────────────────────────────────


@dataclass
class RefRecord:
    """One parsed reference (an external Work stub). ``doi`` is set when GROBID/CrossRef resolves it."""

    ref_id: str  # GROBID's xml:id, e.g. "b17"
    raw: str  # the raw reference string (for CrossRef query + display)
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    journal: str | None = None
    published_date: str | None = None
    doi: str | None = None


@dataclass
class Citation:
    """An in-text citation marker linking body text → a reference (GROBID ``<ref type='bibr'>``)."""

    marker: str  # the marker text, e.g. "[17]"
    target_ref_id: str  # the RefRecord.ref_id it points at


@dataclass
class GrobidDoc:
    """The structured output of one GROBID parse: root identity + references + in-text citations."""

    title: str | None = None
    authors: list[str] = field(default_factory=list)
    journal: str | None = None
    doi: str | None = None
    published_date: str | None = None
    abstract: str | None = None  # header abstract (TEI profileDesc/abstract) — used to LOCATE + tag
    references: list[RefRecord] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)


@dataclass
class CrossRefMatch:
    doi: str
    title: str | None
    published_date: str | None
    citation_count: int | None
    score: float
    journal: str | None = None
    crossref_type: str | None = None  # "journal-article" | "posted-content" (preprint) | …


# ── pure: date helpers ──────────────────────────────────────────────────────────────────────────


def published_date_from_dateparts(date_parts: list) -> str | None:
    """CrossRef ``date-parts`` ([[2021, 8, 14]]) → a partial-precision ISO string ("2021-08-14")."""
    if not date_parts or not date_parts[0]:
        return None
    parts = date_parts[0]
    # CrossRef may emit null members for a registered-but-undated item (e.g. [[null]] or [[2021, null]]);
    # treat a null/missing year as no date, and stop at the first null month/day rather than int(None).
    if parts[0] is None:
        return None
    out = f"{int(parts[0]):04d}"
    if len(parts) >= 2 and parts[1] is not None:
        out += f"-{int(parts[1]):02d}"
        if len(parts) >= 3 and parts[2] is not None:
            out += f"-{int(parts[2]):02d}"
    return out


# ── pure: TEI parsing ───────────────────────────────────────────────────────────────────────────


def _text(el) -> str | None:
    if el is None:
        return None
    s = " ".join(el.itertext()).strip()
    s = re.sub(r"\s+", " ", s)
    return s or None


def _authors(parent) -> list[str]:
    """Display names from a TEI ``<author>`` / ``<persName>`` subtree."""
    names = []
    for pers in parent.findall(".//t:author/t:persName", _TEI_NS):
        fore = " ".join(_text(f) or "" for f in pers.findall("t:forename", _TEI_NS)).strip()
        sur = _text(pers.find("t:surname", _TEI_NS)) or ""
        full = (fore + " " + sur).strip()
        if full:
            names.append(full)
    return names


def _date_from_bibl(bibl) -> str | None:
    date_el = bibl.find(".//t:date", _TEI_NS)
    if date_el is not None and date_el.get("when"):
        return date_el.get("when")  # GROBID emits ISO "when", already partial-precision
    return None


def _doi_from_bibl(bibl) -> str | None:
    for idno in bibl.findall(".//t:idno", _TEI_NS):
        if (idno.get("type") or "").upper() == "DOI" and idno.text:
            return idno.text.strip().lower()
    return None


def parse_tei(tei_xml: str) -> GrobidDoc:
    """Parse a GROBID TEI document into a :class:`GrobidDoc` (header identity + refs + citations)."""
    from lxml import etree

    root = etree.fromstring(tei_xml.encode("utf-8") if isinstance(tei_xml, str) else tei_xml)

    doc = GrobidDoc()

    header = root.find(".//t:teiHeader", _TEI_NS)
    if header is not None:
        doc.title = _text(header.find(".//t:titleStmt/t:title", _TEI_NS))
        src = header.find(".//t:sourceDesc/t:biblStruct", _TEI_NS)
        if src is not None:
            doc.authors = _authors(src)
            doc.doi = _doi_from_bibl(src)
            doc.published_date = _date_from_bibl(src)
            doc.journal = _text(src.find(".//t:monogr/t:title", _TEI_NS))
        doc.abstract = _text(header.find(".//t:profileDesc/t:abstract", _TEI_NS))

    # reference list
    for bibl in root.findall(".//t:back//t:listBibl/t:biblStruct", _TEI_NS):
        ref_id = bibl.get("{http://www.w3.org/XML/1998/namespace}id") or ""
        title = _text(bibl.find(".//t:analytic/t:title", _TEI_NS)) or _text(
            bibl.find(".//t:monogr/t:title", _TEI_NS)
        )
        raw = _text(bibl.find(".//t:note[@type='raw_reference']", _TEI_NS)) or title or ""
        doc.references.append(
            RefRecord(
                ref_id=ref_id,
                raw=raw,
                title=title,
                authors=_authors(bibl),
                journal=_text(bibl.find(".//t:monogr/t:title", _TEI_NS)),
                published_date=_date_from_bibl(bibl),
                doi=_doi_from_bibl(bibl),
            )
        )

    # in-text citation markers
    for ref in root.findall(".//t:text//t:ref[@type='bibr']", _TEI_NS):
        target = (ref.get("target") or "").lstrip("#")
        marker = _text(ref)
        if target and marker:
            doc.citations.append(Citation(marker=marker, target_ref_id=target))

    return doc


# ── pure: CrossRef matching (score-gated) ─────────────────────────────────────────────────────────


def crossref_match(item: dict, *, min_score: float) -> CrossRefMatch | None:
    """Map one CrossRef ``message.items[i]`` to a :class:`CrossRefMatch`, gated on ``score``.

    Below the gate → ``None`` (abstain): no low-confidence DOI is ever asserted (ADR-0003 §2).
    """
    if not item:
        return None
    score = float(item.get("score") or 0.0)
    if score < min_score:
        return None
    doi = (item.get("DOI") or "").strip().lower()
    if not doi:
        return None
    title = item.get("title") or []
    issued = item.get("issued", {}).get("date-parts") or item.get("published", {}).get("date-parts")
    container = item.get("container-title") or []
    return CrossRefMatch(
        doi=doi,
        title=title[0] if title else None,
        published_date=published_date_from_dateparts(issued),
        citation_count=item.get("is-referenced-by-count"),
        score=score,
        journal=container[0] if container else None,
        crossref_type=item.get("type"),
    )


def _title_sim(a: str | None, b: str | None) -> float:
    """Character-trigram overlap coefficient between two titles. Character n-grams are robust to the
    tokenization noise that wrecks *word* overlap on physics titles — chemical-formula spacing
    (``Co 2 MnSi`` vs ``Co2MnSi``, ``La 0 . 7 Sr 0 . 3 MnO 3``), hyphenation (``half-metal``), and
    punctuation all dissolve once non-alphanumerics are stripped."""

    def grams(s: str | None) -> set[str]:
        t = re.sub(r"[^a-z0-9]", "", (s or "").lower())
        return {t[i : i + 3] for i in range(len(t) - 2)}

    ga, gb = grams(a), grams(b)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / min(len(ga), len(gb))


# CrossRef record types that are NOT the work itself — a paper's supplementary-info ``component``
# (``…​.s001``) and ``dataset`` records share the work's title and would otherwise trip false ambiguity.
_NONWORK_TYPES = frozenset({"component", "dataset"})


def _surname(name: str | None) -> str:
    toks = re.findall(
        r"[^\W\d_]+", name or "", re.UNICODE
    )  # letter runs (handles "S Becker", "Kläui")
    return toks[-1].lower() if toks else ""


def _author_overlap(our_authors: list[str] | None, item: dict) -> float:
    """Surname overlap coefficient between our author list and a CrossRef candidate's authors."""
    ours = {s for s in (_surname(a) for a in (our_authors or [])) if s}
    cand = {(a.get("family") or "").lower() for a in item.get("author", []) if a.get("family")}
    if not ours or not cand:
        return 0.0
    return len(ours & cand) / min(len(ours), len(cand))


def _cand_year(item: dict) -> int | None:
    dp = (item.get("issued") or {}).get("date-parts") or (item.get("published") or {}).get(
        "date-parts"
    )
    try:
        return int(dp[0][0])
    except Exception:
        return None


def classify_crossref(
    items: list[dict],
    *,
    min_score: float = 80.0,
    margin: float = 0.15,
    verify_title: str | None = None,
    min_title_sim: float = 0.9,
    peer_margin: float = 0.05,
    verify_authors: list[str] | None = None,
    verify_year: int | None = None,
    confirm_title_floor: float = 0.7,
    min_author_overlap: float = 0.7,
    year_tol: int = 1,
) -> dict:
    """Three-way DOI outcome from CrossRef's top-N candidates (ADR-0005). Pure — no I/O.

    CrossRef's ``score`` is an unbounded, query-dependent relevance score, *not* a probability. Two
    regimes:

    * **``verify_title`` given** (we know the work's own title): gate on **title similarity** (candidate
      vs ours), far more trustworthy than the raw score where the right work can rank below a look-alike.
      Confident = one clear winner; ambiguous = ≥2 genuine peers; abstain = none clears ``min_title_sim``.
      A "peer" is a candidate within ``peer_margin`` of the best *and* above ``min_title_sim`` — a
      look-alike scoring just under the winner is not a peer. Among ≥2 peers, a single
      ``journal-article`` is taken as the canonical work (dedups journal vs preprint/proceedings).
    * **no ``verify_title``**: fall back to the **score gate + relative margin** (a rival counts if its
      score ≥ ``(1 - margin)`` × top score).

    ``component``/``dataset`` records are dropped first (a paper's own supplementary entry is not a
    rival). Returns ``{"outcome", "match", "candidates"}``.
    """
    items = [
        it for it in (items or []) if it and it.get("DOI") and it.get("type") not in _NONWORK_TYPES
    ]
    if not items:
        return {"outcome": "abstain", "match": None, "candidates": []}

    if verify_title:

        def _ok(it: dict, ts: float) -> bool:
            if ts >= min_title_sim:  # strong title alone
                return True
            # author+year CONFIRMS a moderate title (the arXiv-vs-published / erratum / reworded case).
            # NEVER an author-only override: this corpus is one research group, so the same author set
            # recurs across *different* papers — author identity is a weak signal on its own.
            if ts >= confirm_title_floor and verify_authors and verify_year is not None:
                y = _cand_year(it)
                return (
                    _author_overlap(verify_authors, it) >= min_author_overlap
                    and y is not None
                    and abs(y - verify_year) <= year_tol
                )
            return False

        scored = [(it, _title_sim(verify_title, (it.get("title") or [""])[0])) for it in items]
        good = [(it, ts) for it, ts in scored if _ok(it, ts)]
        if not good:
            return {"outcome": "abstain", "match": None, "candidates": []}
        best = max(ts for _, ts in good)
        peers = [it for it, ts in good if ts >= best - peer_margin]
        if len(peers) == 1:
            return {
                "outcome": "confident",
                "match": crossref_match(peers[0], min_score=0.0),
                "candidates": [],
            }
        ja = [it for it in peers if it.get("type") == "journal-article"]
        if len(ja) == 1:  # the canonical journal version among preprint/proceedings peers
            return {
                "outcome": "confident",
                "match": crossref_match(ja[0], min_score=0.0),
                "candidates": [],
            }
        cands = [
            {"doi": it["DOI"].strip().lower(), "score": float(it.get("score") or 0.0)}
            for it in peers[:3]
        ]
        return {"outcome": "ambiguous", "match": None, "candidates": cands}

    top = items[0]
    top_score = float(top.get("score") or 0.0)
    if top_score < min_score:
        return {"outcome": "abstain", "match": None, "candidates": []}
    rivals = [it for it in items if float(it.get("score") or 0.0) >= (1.0 - margin) * top_score]
    if len(rivals) >= 2:  # the top itself is always in `rivals`; ≥2 ⇒ a real competitor is close
        cands = [
            {"doi": it["DOI"].strip().lower(), "score": float(it.get("score") or 0.0)}
            for it in rivals[:3]
        ]
        return {"outcome": "ambiguous", "match": None, "candidates": cands}
    return {
        "outcome": "confident",
        "match": crossref_match(top, min_score=min_score),
        "candidates": [],
    }


# ── pure: tree enrichment ─────────────────────────────────────────────────────────────────────────


_CITE_HOST_TYPES = ("paragraph", "list-item", "footnote")
# A canonical numeric citation marker: [17], [3,14-16], [9-13,21]. citation_normalize emits exactly
# this SPACE-FREE form at parse time, so native-bracket and (normalized) superscript papers share one
# shape. The no-space rule is also the precision guard separating a citation from an inline data array
# ("[16, 8, 4, 2, 1]" — reservoir layer sizes), which carries comma-spaces and is thus skipped.
_BRACKET_CITE_RE = re.compile(r"\[(\d+(?:[-–]\d+)?(?:,\d+(?:[-–]\d+)?)*)\]")


def _ascending(run: str) -> bool:
    """A citation list runs low→high ("[3,14-16]"); a descending run ("[16,8,4,2,1]") is a data array."""
    firsts = [int(re.match(r"\d+", part).group()) for part in run.split(",") if part]
    return all(a <= b for a, b in zip(firsts, firsts[1:]))


# The number a bibliography entry declares for ITSELF at the start of its raw string:
# "[15] A. Author …", "(15) …", "15. …", "15: …", "15) …". Capped at 3 digits so a leading year
# ("2021.") can never masquerade as a reference number.
_REF_LABEL_RE = re.compile(r"^\s*(?:\[(\d{1,3})\]|\((\d{1,3})\)|(\d{1,3})\s*[.:)\]])")


def _declared_ref_numbers(refs: list[BlockNode]) -> dict[int, str] | None:
    """Map each reference's *declared* bibliography number → node id; ``None`` if unnumbered.

    Issue 0006: linking ``[k]`` to the *k-th parsed* reference trusts GROBID to have dropped nothing —
    one mid-list miss shifts every later edge off-by-one, silently. The printed number at the head of
    each raw entry is the author-typeset truth, so when the bibliography carries its own numbers we key
    on those instead. Precision gates: declared numbers must be unique and present on at least half the
    entries (else the style is unnumbered/untrustworthy → caller falls back to positional order).
    """
    declared: dict[int, str] = {}
    for node in refs:
        m = _REF_LABEL_RE.match(node.text or node.attrs.get("raw") or "")
        if not m:
            continue
        num = int(next(g for g in m.groups() if g))
        if num in declared:
            return None  # duplicate declared numbers — distrust the labels entirely
        declared[num] = node.id
    if len(declared) < max(2, len(refs) // 2):
        return None
    return declared


def link_bracket_citations(root: BlockNode, *, n_refs: int) -> int:
    """Add ``cites`` edges for every ``[N]`` marker in prose. Returns the count.

    Scans each prose leaf for canonical (space-free, ascending) bracket markers, expands ranges/lists,
    and links each number *k* to its reference node — **by the bibliography's own declared numbers**
    when it carries them (:func:`_declared_ref_numbers`; robust to GROBID dropping an entry), by
    positional order (``<root>/ref{k}``) only for unnumbered lists. The edge is anchored on the
    bracket's char-span. **Precision over recall:** a number with no matching reference yields no edge
    (abstain, never fabricate); non-citation bracketed numerics (data arrays) are screened by the
    space + ascending guards.
    """
    from .superscript_cites import expand_numbers

    id_set = {n.id for n in root.walk()}
    declared = _declared_ref_numbers([n for n in root.walk() if n.type == "reference"])
    added = 0
    for n in root.walk():
        if n.type not in _CITE_HOST_TYPES or not n.text or not n.prov:
            continue
        base = n.prov[0].char_span[0]
        for mm in _BRACKET_CITE_RE.finditer(n.text):
            if not _ascending(mm.group(1)):
                continue
            span = (base + mm.start(), base + mm.end())
            for num in expand_numbers(mm.group(1)):
                if declared is not None:
                    target = declared.get(num)
                    if target is None:
                        continue  # declared numbering has no such entry — abstain
                else:
                    if not (1 <= num <= n_refs):
                        continue
                    target = f"{root.id}/ref{num}"
                if target not in id_set:
                    continue
                if any(
                    e.type == "cites" and e.target == target and e.marker_span == span
                    for e in n.edges
                ):
                    continue
                n.edges.append(Edge(type="cites", target=target, marker_span=span))
                added += 1
    return added


_WORD_RE = re.compile(r"[a-z0-9]+")


def _word_tokens(s: str | None) -> list[str]:
    return _WORD_RE.findall((s or "").lower())


def _front_region(root: BlockNode):
    """Yield front-matter nodes: everything down to (excluding) the first *real body* section.

    The abstract sits between the title block and the first numbered section. An ``abstract``-titled
    section heading is itself front matter, so we don't stop at it — only at the first section whose
    title isn't abstract-like (e.g. ``I. INTRODUCTION``). This bounds the search so a later body
    paragraph that happens to echo the abstract can never be mistaken for it.
    """
    for n in root.walk():
        if n.type in ("section", "chapter", "subsection"):
            title = (n.text or n.attrs.get("title") or "").strip().lower()
            if "abstract" not in title:
                return
        yield n


def tag_abstract(
    root: BlockNode, abstract_text: str | None, *, min_tokens: int = 12, overlap: float = 0.7
) -> int:
    """Relabel the front-matter paragraph(s) GROBID identified as the abstract to type ``abstract``.

    GROBID gives a clean abstract *string* but no PDF coordinates; the structural parse already
    captured the abstract as an untyped ``paragraph`` *with* provenance. So we use GROBID's string to
    **locate** that paragraph and relabel its type — keeping the page/bbox/char-span. **Precision-first:**
    a front-region paragraph is the abstract only if it overlaps GROBID's abstract strongly, scored by
    the **overlap coefficient** ``|P∩A| / min(|P|,|A|)`` — symmetric, so it's unmoved by one side
    carrying extra words (a trailing sentence GROBID trimmed, or formula tokens that split differently,
    ``TmFeO 3`` vs ``TmFeO3``). The intro shares some vocabulary but never most of it, so it stays a
    paragraph; author/affiliation/date lines are screened by ``min_tokens``. Handles a 1- or 2-paragraph
    abstract. Returns the count relabeled (0 ⇒ caller keeps GROBID's string as an unlocated fallback).
    Never raises.
    """
    abs_tokens = set(_word_tokens(abstract_text))
    if len(abs_tokens) < min_tokens:
        return 0
    tagged = 0
    for n in _front_region(root):
        # "abstract" is accepted alongside "paragraph" so a re-run still *finds* the node it already
        # relabeled — otherwise a second enrichment would return 0 and the caller would demote a
        # located abstract to the unlocated-string fallback (idempotency).
        if n.type not in ("paragraph", "abstract") or not n.text:
            continue
        toks = set(_word_tokens(n.text))
        if len(toks) < min_tokens:
            continue
        if len(toks & abs_tokens) / min(len(toks), len(abs_tokens)) >= overlap:
            n.type = "abstract"
            tagged += 1
    return tagged


def enrich_tree(root: BlockNode, gdoc: GrobidDoc) -> BlockNode:
    """Phase 1 (ADR-0005) — attach the GROBID bibliography onto an existing Docling tree, in place.

    Sets the root's citable identity, appends a back-matter ``references`` subtree of ``reference``
    nodes, and adds ``cites`` edges from in-text markers to those nodes (literal marker alignment;
    abstain when not found). **GROBID-only, no network beyond the local service**: the only DOIs
    written are the ones GROBID itself extracted (``idno``). Everything CrossRef — resolving the
    remaining reference DOIs, the header identity, citation counts — is Phase 2,
    :func:`ref_consolidate`, a separate resumable step (``python -m lit_rag.corpusops consolidate``).
    Returns ``root``.
    """

    # 1) root identity — fill, never clobber a value Docling already had with an empty GROBID one
    if gdoc.doi:
        root.attrs["doi"] = gdoc.doi
        root.attrs["citable_key"] = gdoc.doi  # DOI becomes the spine key once resolved
    if gdoc.published_date:
        root.attrs["published_date"] = gdoc.published_date
    if gdoc.authors:
        root.attrs.setdefault("authors", gdoc.authors)
    if gdoc.journal:
        root.attrs.setdefault("journal", gdoc.journal)
    if gdoc.title and not root.attrs.get("title"):
        root.attrs["title"] = gdoc.title
    # abstract — relabel the located body paragraph (keeps provenance); fall back to carrying GROBID's
    # string on the root only when it can't be located, so the summary is never lost. Empty on both ⇒
    # no abstract in the source → an "unwritten summary" the catalog later flags for generation.
    if gdoc.abstract:
        if tag_abstract(root, gdoc.abstract):
            root.attrs["abstract_source"] = "located"
        else:
            root.attrs["abstract"] = gdoc.abstract
            root.attrs["abstract_source"] = "grobid-unlocated"

    # 2) resolve each reference (GROBID DOI, else CrossRef score-gated) and build reference nodes.
    #    Idempotent by REPLACEMENT: a re-run drops the previous enrichment's references container and
    #    the cites edges pointing into it before re-adding — running bib twice must equal running it
    #    once, never a doubled bibliography with duplicate ids.
    refs_id = f"{root.id}/references"
    ref_prefix = f"{root.id}/ref"
    if any(c.id == refs_id for c in root.children):
        root.children = [c for c in root.children if c.id != refs_id]
        for n in root.walk():
            n.edges = [
                e for e in n.edges if not (e.type == "cites" and e.target.startswith(ref_prefix))
            ]
    refs_container = BlockNode(id=refs_id, type="section", text="References")
    ref_node_by_tei: dict[str, BlockNode] = {}
    for i, ref in enumerate(gdoc.references, 1):
        node = BlockNode(id=f"{root.id}/ref{i}", type="reference", text=ref.raw or None)
        attrs: dict = {"raw": ref.raw}
        if ref.title:
            attrs["title"] = ref.title
        if ref.authors:
            attrs["authors"] = ref.authors
        if ref.journal:
            attrs["journal"] = ref.journal
        if ref.published_date:
            attrs["published_date"] = ref.published_date

        if ref.doi:  # GROBID's own idno only — CrossRef resolution is Phase 2 (ref_consolidate)
            attrs["doi"] = ref.doi

        node.attrs = attrs
        refs_container.children.append(node)
        if ref.ref_id:
            ref_node_by_tei[ref.ref_id] = node
    if refs_container.children:
        root.children.append(refs_container)

    # 3) cites edges — uniform over the now-canonical [N] markers (superscripts were normalized to
    #    brackets at parse time, so bracket-native and superscript papers link identically here).
    link_bracket_citations(root, n_refs=len(gdoc.references))

    return root


def collect_catalog_signals(root: BlockNode) -> list[dict]:
    """Harvest the catalog-only signals (citation count + as-of) per citable node, *before* stripping.

    Returns one record per citable node (the root + every resolved reference) that carries a citation
    count. This is the sidecar the store ingest applies straight into the catalog — the path that gets
    the drifting count into the DB *without* ever writing it into ``tree.json`` (design §3.7).
    """
    out: list[dict] = []
    for n in root.walk():
        if n.type not in ("document", "reference"):
            continue
        key = n.attrs.get("citable_key") or n.attrs.get("doi")
        if not key:
            continue
        cc = n.attrs.get("citation_count")
        if cc is None:
            continue
        out.append(
            {
                "citable_key": key,
                "citation_count": cc,
                "citation_count_as_of": n.attrs.get("citation_count_as_of"),
            }
        )
    return out


def strip_catalog_only(root: BlockNode) -> BlockNode:
    """Remove catalog-only attrs (``citation_count`` + as-of) from every node, in place.

    Call this AFTER projecting the enriched tree into the catalog and BEFORE writing ``tree.json`` —
    the drifting citation count must never be frozen into the canonical tree (design §3.7).
    """
    for n in root.walk():
        for k in CATALOG_ONLY_ATTRS:
            n.attrs.pop(k, None)
    return root


_ARXIV_RE = re.compile(r"ar[Xx]iv[:\s]\s*(\d{4}\.\d{4,5})(?:v\d+)?")


def find_arxiv_id(root: BlockNode) -> str | None:
    """The arXiv identifier stamped on the PDF (``arXiv:2407.00539``), scanned from node text.

    37 % of this corpus are arXiv PDFs, so the paper's *own* metadata is the preprint's — the published
    title/DOI may differ. The arXiv id is the deterministic bridge: :func:`arxiv_query` exchanges it for
    the **published** DOI the author registered, no fuzzy matching needed."""
    for n in root.walk():
        if n.text:
            m = _ARXIV_RE.search(n.text)
            if m:
                return m.group(1)
    return None


def _header_query(root: BlockNode) -> str | None:
    """A reference-like CrossRef query from the header GROBID extracted: authors + title + journal +
    year. A bare title scores too low and can rank below a look-alike; the full bibliographic string
    ranks the right work first (then :func:`classify_crossref` verifies it by title)."""
    a = root.attrs
    title = a.get("title")
    if not title:
        return None
    parts: list[str] = []
    if a.get("authors"):
        parts.append(" ".join(a["authors"][:5]))
    parts.append(title)
    if a.get("journal"):
        parts.append(a["journal"])
    year = (a.get("published_date") or "")[:4]
    if year:
        parts.append(year)
    return " ".join(parts).strip()


def ref_consolidate(
    root: BlockNode,
    *,
    query_fn,
    arxiv_fn=None,
    doi_fn=None,
    min_score: float = 80.0,
    margin: float = 0.15,
    do_references: bool = True,
    do_header: bool = True,
    max_workers: int = 1,
    as_of: datetime | None = None,
) -> dict:
    """Phase 2 (ADR-0005) — resolve DOIs on a Phase-1 tree via CrossRef, three-way. Returns stats.

    The **external** half of the split: GROBID gave reference *strings* + a header; this matches them
    to canonical DOIs. ``query_fn(text) -> list[item]`` is the injected CrossRef call (top-N candidates;
    :func:`crossref_candidates` in production, a stub in tests). **Idempotent** — skips any node that
    already has a ``doi``, so it resumes after an interruption and never double-resolves.

    Per :func:`classify_crossref`: *confident* writes ``doi`` (+ promotes the root's ``citable_key`` and
    rides catalog-only ``citation_count``); *ambiguous* writes ``doi_candidates`` + ``doi_ambiguous``
    and **no** ``doi`` — so it produces no catalog row or ``cites`` edge (uncertainty stays off the
    committed graph), awaiting a later disambiguation pass; *abstain* writes nothing. ``do_header`` /
    ``do_references`` gate the two scopes (e.g. header-only is the cheap dedup-unlocking pass).

    ``max_workers`` > 1 fans the references' CrossRef lookups out over a thread pool, so a whole
    bibliography resolves in seconds instead of one serial round-trip per reference (the lookups are
    network-bound and release the GIL). Only the slow ``query_fn`` calls run concurrently; classification
    and the node/``stats`` mutations stay single-threaded and in tree order, so the result is **identical
    and deterministic** regardless of worker count. The header is a single query and stays serial.
    """
    as_of = as_of or datetime.now(timezone.utc)
    as_of_iso = as_of.isoformat()
    stats = {"queried": 0, "confident": 0, "ambiguous": 0, "abstain": 0, "arxiv": 0}

    def _year(node: BlockNode) -> int | None:
        y = (node.attrs.get("published_date") or "")[:4]
        return int(y) if y.isdigit() else None

    def _apply(node: BlockNode, m: "CrossRefMatch", *, is_root: bool, preprint: bool) -> None:
        node.attrs["doi"] = m.doi
        node.attrs.pop("doi_candidates", None)  # a re-run resolved a previously-ambiguous node
        node.attrs.pop("doi_ambiguous", None)
        if is_root:
            node.attrs["citable_key"] = m.doi  # promote hash → DOI (the dedup/linking spine)
        if m.title:
            node.attrs.setdefault("title", m.title)
        if m.journal:
            node.attrs["journal"] = m.journal
        if m.published_date:
            node.attrs["published_date"] = m.published_date
        node.attrs["is_preprint"] = (
            preprint  # so a later refresh can promote it to the published version
        )
        if m.citation_count is not None:
            node.attrs["citation_count"] = m.citation_count  # CATALOG-ONLY (stripped pre-disk)
            node.attrs["citation_count_as_of"] = as_of_iso

    def _classify_apply(
        node: BlockNode,
        items: list,
        verify_title: str | None,
        verify_authors: list[str] | None,
        *,
        is_root: bool,
    ) -> None:
        """Classify pre-fetched CrossRef ``items`` and write the outcome onto ``node`` — pure CPU + a
        single-node mutation, no I/O. Kept off the worker threads so ``stats`` needs no lock."""
        stats["queried"] += 1
        res = classify_crossref(
            items,
            min_score=min_score,
            margin=margin,
            verify_title=verify_title,
            verify_authors=verify_authors,
            verify_year=_year(node),
        )
        stats[res["outcome"]] += 1
        if res["outcome"] == "confident":
            m = res["match"]
            _apply(node, m, is_root=is_root, preprint=m.crossref_type == "posted-content")
        elif res["outcome"] == "ambiguous":
            node.attrs["doi_candidates"] = res["candidates"]
            node.attrs["doi_ambiguous"] = True

    def _resolve(
        node: BlockNode,
        query_text: str | None,
        verify_title: str | None,
        verify_authors: list[str] | None,
        *,
        is_root: bool,
    ) -> None:
        if not query_text:
            return
        _classify_apply(node, query_fn(query_text), verify_title, verify_authors, is_root=is_root)

    def _resolve_via_arxiv() -> bool:
        """Deterministic bridge: arXiv id → the published DOI the author registered. Returns True if it
        set the root identity (no fuzzy matching needed); False to fall through to CrossRef title match."""
        aid = find_arxiv_id(root)
        if aid:
            root.attrs["arxiv_id"] = aid
        if not (aid and arxiv_fn):
            return False
        info = arxiv_fn(aid) or {}
        pub_doi = info.get("doi")
        if not pub_doi:  # still a preprint with no published DOI yet — let CrossRef try
            return False
        item = doi_fn(pub_doi) if doi_fn else None
        m = crossref_match(item, min_score=0.0) if item else None
        if m is None:  # arXiv gave the DOI but CrossRef has no metadata — assert the DOI minimally
            m = CrossRefMatch(
                doi=pub_doi.strip().lower(),
                title=None,
                published_date=info.get("published_date"),
                citation_count=None,
                score=0.0,
                journal=info.get("journal_ref"),
            )
        _apply(
            root, m, is_root=True, preprint=False
        )  # the published version, by author registration
        stats["confident"] += 1
        stats["arxiv"] += 1
        return True

    if do_references:
        # the raw reference string already carries authors+title+journal+year; verify against
        # GROBID's parsed reference title + authors when present.
        pending = [
            (n, n.attrs.get("raw") or n.text)
            for n in root.walk()
            if n.type == "reference" and not n.attrs.get("doi")
        ]
        pending = [(n, q) for n, q in pending if q]
        if max_workers > 1 and len(pending) > 1:
            # fan the network-bound lookups out; classify+apply below stays serial + in tree order.
            with ThreadPoolExecutor(max_workers=min(max_workers, len(pending))) as ex:
                items_by_node = list(ex.map(lambda nq: query_fn(nq[1]), pending))
            for (n, _q), items in zip(pending, items_by_node):
                _classify_apply(
                    n, items, n.attrs.get("title"), n.attrs.get("authors"), is_root=False
                )
        else:
            for n, q in pending:
                _resolve(n, q, n.attrs.get("title"), n.attrs.get("authors"), is_root=False)
    if do_header and not root.attrs.get("doi"):
        # arXiv bridge first (deterministic, published DOI by author registration), else CrossRef match
        if not _resolve_via_arxiv():
            _resolve(
                root,
                _header_query(root),
                root.attrs.get("title"),
                root.attrs.get("authors"),
                is_root=True,
            )
        # record WHEN the external identity was last consolidated (whatever the outcome) — lets a
        # periodic job find stale entries to refresh citation counts and promote preprints (design §3.7).
        root.attrs["metadata_updated_at"] = as_of_iso
    return stats


# ── thin I/O clients (not exercised by the offline gate) ──────────────────────────────────────────


class GrobidClient:
    """Thin client for a GROBID service (the compose container, localhost:8070)."""

    def __init__(self, base_url: str = "http://127.0.0.1:8070", timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def process_fulltext(self, pdf_bytes: bytes, *, consolidate: bool = False) -> str:
        """POST a PDF to ``/api/processFulltextDocument`` → TEI XML.

        Per ADR-0005 this is **Phase 1 — internal structure only**: ``consolidate=False`` keeps
        GROBID from calling CrossRef itself (the per-reference consolidation that made each parse
        ~37 s and OOM-crashed the service mid-corpus). Header/reference DOIs are resolved separately
        in Phase 2 (:func:`ref_consolidate`). ``includeRawCitations`` stays on — Phase 2 needs the raw
        strings. Set ``consolidate=True`` only for a one-off comparison.
        """
        import httpx

        flag = "1" if consolidate else "0"
        files = {"input": ("doc.pdf", pdf_bytes, "application/pdf")}
        data = {
            "consolidateHeader": flag,
            "consolidateCitations": flag,
            "includeRawCitations": "1",
        }
        r = httpx.post(
            f"{self.base_url}/api/processFulltextDocument",
            files=files,
            data=data,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.text


def crossref_candidates(
    bibliographic: str, *, mailto: str | None = None, rows: int = 3, timeout: float = 30.0
) -> list[dict]:
    """Query CrossRef ``/works`` for a string; return the **top-N** ``message.items`` (ADR-0005).

    Phase 2's :func:`ref_consolidate` needs more than the single best hit — it compares #1 vs #2 to
    detect an ambiguous match, so this returns the ranked list (``rows`` candidates) rather than just
    the top. Polite pool when ``mailto`` is set.
    """
    import httpx

    params = {"query.bibliographic": bibliographic, "rows": str(rows)}
    if mailto:
        params["mailto"] = mailto
    headers = {"User-Agent": f"lit-rag/0.1 (mailto:{mailto})" if mailto else "lit-rag/0.1"}
    r = httpx.get("https://api.crossref.org/works", params=params, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json().get("message", {}).get("items", [])


def crossref_by_doi(doi: str, *, mailto: str | None = None, timeout: float = 30.0) -> dict:
    """Fetch a single CrossRef work *by DOI* → the ``message`` item (full metadata + citation count).

    Used after :func:`arxiv_query` hands back a published DOI: we have the DOI for certain, we just want
    its metadata. Returns ``{}`` if not found."""
    import httpx

    headers = {"User-Agent": f"lit-rag/0.1 (mailto:{mailto})" if mailto else "lit-rag/0.1"}
    params = {"mailto": mailto} if mailto else None
    r = httpx.get(
        f"https://api.crossref.org/works/{doi}", params=params, headers=headers, timeout=timeout
    )
    if r.status_code == 404:
        return {}
    r.raise_for_status()
    return r.json().get("message", {})


def arxiv_query(arxiv_id: str, *, timeout: float = 30.0) -> dict:
    """Query the arXiv API for an id → ``{"doi", "journal_ref", "published_date"}``.

    ``doi`` is the **published** DOI the author registered on arXiv (the deterministic preprint→published
    bridge), or ``None`` if the preprint isn't published yet. Returns ``{}`` on no entry."""
    import httpx
    from lxml import etree

    r = httpx.get(
        "https://export.arxiv.org/api/query",
        params={"id_list": arxiv_id},
        timeout=timeout,
        follow_redirects=True,
    )
    r.raise_for_status()
    ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    entry = etree.fromstring(r.content).find("a:entry", ns)
    if entry is None:
        return {}

    def _t(tag: str) -> str | None:
        el = entry.find(tag, ns)
        return el.text.strip() if el is not None and el.text else None

    doi = _t("arxiv:doi")
    pub = _t("a:published")
    return {
        "doi": doi.lower() if doi else None,
        "journal_ref": _t("arxiv:journal_ref"),
        "published_date": pub[:10] if pub else None,
    }
