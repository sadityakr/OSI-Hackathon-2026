"""Figures of a paper, as the agent sees them.

The agent asks three things of a paper: which figures does it have, which paragraphs talk about a
given figure, and which panel shows a Raman spectrum (answered by a vision model in ``panels.py``,
not here). This module turns a parsed tree into plain records for those questions.

    from iopic_bond.arxiv import fetch_pdf
    from iopic_bond.figures import extract_figures

    pdf = fetch_pdf("2211.12939", "papers/2211.12939/paper.pdf")
    figs = extract_figures(pdf, "papers/2211.12939/parsed")
    for f in figs:
        print(f.label, f.image_path, f.caption[:80], len(f.mentions))
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .tracing import traced
from .pdf import BlockNode, parse_pdf


@dataclass
class Figure:
    paper_id: str          # content hash of the parsed document (stable per PDF bytes)
    node_id: str           # tree node id, e.g. <hash>/sec3/fig2
    label: Optional[str]   # "Figure 2" as printed in the caption, None if no caption matched
    caption: str
    page: Optional[int]
    image_path: Optional[Path]   # absolute path to figures/figN.png, None if the crop failed
    mentions: list[str] = field(default_factory=list)  # paragraphs that reference this figure

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["image_path"] = str(self.image_path) if self.image_path else None
        return d


def _mentions(root: BlockNode) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for n in root.walk():
        if not n.text:
            continue
        for e in n.edges:
            if e.type == "references-figure":
                out.setdefault(e.target, []).append(n.text)
    return out


def figures_from_tree(root: BlockNode, doc_dir: Path) -> list[Figure]:
    """Flatten the figure nodes of a parsed tree into ``Figure`` records."""
    mentions = _mentions(root)
    out: list[Figure] = []
    for n in root.walk():
        if n.type != "figure":
            continue
        rel = n.attrs.get("image_path")
        img = (doc_dir / rel) if rel and (doc_dir / rel).exists() else None
        page = n.attrs.get("caption_page") or (n.prov[0].page_no if n.prov else None)
        out.append(Figure(
            paper_id=root.id,
            node_id=n.id,
            label=n.attrs.get("label"),
            caption=(n.attrs.get("caption") or "").strip(),
            page=page,
            image_path=img,
            mentions=mentions.get(n.id, []),
        ))
    return out


@traced("figure.parse")
def extract_figures(pdf_path, parsed_dir, **parse_kwargs) -> list[Figure]:
    """Parse (or load from cache) and return the paper's figures with captions and mentions."""
    root = parse_pdf(pdf_path, parsed_dir, **parse_kwargs)
    doc_dir = Path(parsed_dir) / root.id
    return figures_from_tree(root, doc_dir)


def likely_spectrum_figures(figs: list[Figure]) -> list[Figure]:
    """Cheap caption-based pre-filter before the vision model: keep figures whose caption or
    mentions talk about Raman spectra, phonons or modes. Precision comes from ``panels.py``."""
    keys = ("raman", "spectr", "phonon", "mode", "cm-1", "cm$^{-1}$", "wavenumber", "shift")
    out = []
    for f in figs:
        text = (f.caption + " " + " ".join(f.mentions)).lower()
        if any(k in text for k in keys):
            out.append(f)
    return out
