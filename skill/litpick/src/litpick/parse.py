"""Find the figures in a PDF: caption, page, region, and the paragraphs that discuss each one.

How it works (all with PyMuPDF, on the PDF's own layout, no machine learning):

1. Captions. A text block that STARTS with "Fig. 3", "FIG. 3.", "Figure 3 |", "Figure S2:",
   "Extended Data Fig. 1" and so on. To tell a caption from a sentence such as "Fig. 3 shows ...",
   the number must be followed by punctuation (. : | -) or the keyword must be set in bold.
2. Graphics. Raster images (page.get_image_info) plus vector drawings grouped into clusters
   (page.cluster_drawings). Hairlines that run across the page (rules, table lines) are dropped.
   Clusters closer than a few points are merged, so a multi-panel figure becomes one group.
3. Matching. Each graphics group goes to the nearest caption BELOW it in the same column
   (journals put figure captions under the figure). A group with no caption below goes to the
   nearest caption above. A caption's figure is the union of its groups, grown to take in short
   text blocks at its edge (axis titles, panel letters).
4. Fallback. A caption with no graphics gets the gap between the text above it and the caption
   ("gap"); if even that is too small, the whole page ("page"). The method is stored, so a
   caller can see how sure the region is.
5. Mentions. Every body paragraph that cites "Fig. 3", "Figs. 2 and 3", "Figs. 2-4" or
   "Fig. 3(b)" is kept under each figure it names.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pymupdf

# ---------------------------------------------------------------- captions

_KW = (
    r"(?P<kw>(?:Extended\s+Data\s+|Supplementary\s+|Supporting\s+)?"
    r"(?:FIGURE|Figure|FIG\.?|Fig\.?))"
)
# some arXiv PDFs set a bar between keyword and number ("FIG.| 1."), so it is allowed there too
CAPTION_RX = re.compile(r"^\s*" + _KW + r"(?:\s*\|)?\s*(?P<num>S?\d{1,3})(?P<after>\s*[.:|\u2013\u2014-]?)")
_LABEL_RX = re.compile(CAPTION_RX.pattern, re.I)  # for what a person types: "figure 2", "fig 2"
# a panel after the number: "3(b)", "3(a,c)", "3b", but never " a" from the word "and"
_PANEL = r"(?:\([a-z](?:[,\-\u2013][a-z])*\)|[a-z](?![a-z]))?"
REF_RX = re.compile(
    r"\b(?:Extended\s+Data\s+|Supplementary\s+)?(?:Figs?\.|Figures?|FIGS?\.|FIGURES?)\s*"
    r"(?P<list>S?\d{1,3}" + _PANEL + r"(?:\s*(?:,|and|&|\u2013|-|to)\s*S?\d{1,3}" + _PANEL + r")*)"
)
_NUM_RX = re.compile(r"(S?)(\d{1,3})")
_SENT_RX = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


def _label(kw: str, num: str) -> str:
    kw = kw.lower()
    if kw.startswith("extended"):
        return "ED" + num
    if kw.startswith(("supplementary", "supporting")) and not num.startswith("S"):
        return "S" + num
    return num


def normalise_label(text: str) -> str:
    """'Fig. 2', 'figure 2', '2', 'S1', 'Supplementary Fig. 1', 'Extended Data Fig. 3' -> label."""
    t = text.strip()
    m = _LABEL_RX.match(t)
    if m:
        return _label(m["kw"], m["num"].upper())
    m = re.fullmatch(r"(ED|S)?\s*(\d{1,3})", t, flags=re.I)
    if m:
        return (m[1] or "").upper() + m[2]
    return t


# ---------------------------------------------------------------- data

@dataclass
class Block:
    rect: pymupdf.Rect
    text: str
    lines: int
    bold_start: bool


@dataclass
class Figure:
    label: str
    page: int  # 1-based
    bbox: list[float]  # x0, y0, x1, y1 in PDF points
    caption: str
    method: str  # graphics | gap | page
    mentions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ParsedPdf:
    pages: int
    title_guess: str
    figures: list[Figure]


# ---------------------------------------------------------------- helpers

def _join_lines(lines: list[str]) -> str:
    out = ""
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        last_word = out.rsplit(" ", 1)[-1]
        if out.endswith("-") and ln[:1].islower() and last_word[:-1].isalpha():
            out = out[:-1] + ln  # undo hyphenation at a line break ("magneto-" + "resistance")
        elif out.endswith("-"):
            out = out + ln  # a real compound split at its hyphen ("out-of-" + "plane")
        else:
            out = (out + " " + ln) if out else ln
    return re.sub(r"\s+", " ", out).strip()


def _blocks(page: pymupdf.Page) -> list[Block]:
    out: list[Block] = []
    for b in page.get_text("dict", flags=pymupdf.TEXT_PRESERVE_WHITESPACE)["blocks"]:
        if b.get("type") != 0:
            continue
        lines, first_bold = [], None
        for ln in b["lines"]:
            spans = [s for s in ln["spans"] if s["text"].strip()]
            if not spans:
                continue
            if first_bold is None:
                s = spans[0]
                first_bold = bool(s["flags"] & 16) or "bold" in s["font"].lower()
            lines.append("".join(s["text"] for s in ln["spans"]))
        text = _join_lines(lines)
        if text:
            out.append(Block(pymupdf.Rect(b["bbox"]), text, len(lines), bool(first_bold)))
    return out


def _is_caption(b: Block) -> re.Match | None:
    m = CAPTION_RX.match(b.text)
    if not m:
        return None
    after = m["after"].strip()
    return m if (after or b.bold_start) else None


def _h_overlap(a: pymupdf.Rect, b: pymupdf.Rect) -> float:
    return max(0.0, min(a.x1, b.x1) - max(a.x0, b.x0))


def _same_column(g: pymupdf.Rect, cap: pymupdf.Rect) -> bool:
    ov = _h_overlap(g, cap)
    return ov > 0.25 * min(g.width, cap.width) or ov > 40


def _graphics(page: pymupdf.Page) -> list[pymupdf.Rect]:
    pw, ph = page.rect.width, page.rect.height
    rects: list[pymupdf.Rect] = []
    for info in page.get_image_info():
        r = pymupdf.Rect(info["bbox"]) & page.rect
        if r.width > 20 and r.height > 20:
            rects.append(r)
    try:
        clusters = page.cluster_drawings(x_tolerance=4, y_tolerance=4)
    except Exception:  # very old PyMuPDF or a broken content stream
        clusters = []
    for r in clusters:
        r = pymupdf.Rect(r) & page.rect
        hairline = (r.height < 3 and r.width > 0.3 * pw) or (r.width < 3 and r.height > 0.3 * ph)
        if hairline or r.width * r.height < 400 or (r.width > 0.97 * pw and r.height > 0.97 * ph):
            continue
        rects.append(r)
    # merge rectangles that touch or nearly touch, until nothing changes
    merged = True
    while merged:
        merged = False
        out: list[pymupdf.Rect] = []
        for r in rects:
            for i, o in enumerate(out):
                if (pymupdf.Rect(o.x0 - 8, o.y0 - 8, o.x1 + 8, o.y1 + 8)).intersects(r):
                    out[i] = o | r
                    merged = True
                    break
            else:
                out.append(r)
        rects = out
    return rects


# ---------------------------------------------------------------- main entry

def parse_pdf(path: Path) -> ParsedPdf:
    doc = pymupdf.open(path)
    try:
        return _parse(doc)
    finally:
        doc.close()


def _parse(doc: pymupdf.Document) -> ParsedPdf:
    figures: dict[str, Figure] = {}
    body: list[tuple[int, str]] = []  # (page, paragraph) for mention search
    title_guess = (doc.metadata or {}).get("title", "") or ""

    for pno, page in enumerate(doc, start=1):
        blocks = _blocks(page)
        if pno == 1 and not title_guess and blocks:
            title_guess = blocks[0].text[:200]
        caps: list[tuple[Block, str]] = []
        for b in blocks:
            m = _is_caption(b)
            if m:
                caps.append((b, _label(m["kw"], m["num"])))
            else:
                body.append((pno, b.text))
        if not caps:
            continue

        groups = _graphics(page)
        owned: dict[int, list[pymupdf.Rect]] = {i: [] for i in range(len(caps))}
        for g in groups:
            below = [(c.rect.y0 - g.y1, i) for i, (c, _) in enumerate(caps)
                     if _same_column(g, c.rect) and c.rect.y0 >= g.y1 - 6]
            above = [(g.y0 - c.rect.y1, i) for i, (c, _) in enumerate(caps)
                     if _same_column(g, c.rect) and g.y0 >= c.rect.y1 - 6]
            if below:
                gap, i = min(below)
                if gap < 0.6 * page.rect.height:
                    owned[i].append(g)
                    continue
            if above:
                gap, i = min(above)
                if gap < 120:
                    owned[i].append(g)

        cap_rects = [c.rect for c, _ in caps]
        for i, (cap, label) in enumerate(caps):
            if owned[i]:
                rect = owned[i][0]
                for g in owned[i][1:]:
                    rect |= g
                grow = pymupdf.Rect(rect.x0 - 14, rect.y0 - 14, rect.x1 + 14, rect.y1 + 14)
                for b in blocks:
                    if b.rect in cap_rects or not grow.intersects(b.rect):
                        continue
                    label_like = b.lines <= 2 and b.rect.width < 0.6 * max(rect.width, 1)
                    if label_like or b.rect in grow:
                        rect |= b.rect
                method = "graphics"
            else:
                above_text = [b.rect.y1 for b in blocks
                              if b.rect.y1 <= cap.rect.y0 and _same_column(b.rect, cap.rect)
                              and b.rect not in cap_rects]
                y0 = max(above_text) if above_text else page.rect.y0 + 36
                if cap.rect.y0 - y0 > 60:
                    rect = pymupdf.Rect(cap.rect.x0, y0, cap.rect.x1, cap.rect.y0)
                    method = "gap"
                else:
                    rect = pymupdf.Rect(page.rect)
                    method = "page"
            fig = Figure(label, pno, [round(v, 1) for v in rect], cap.text, method)
            old = figures.get(label)
            # keep the first caption of a number, unless a later one has a better region
            if old is None or (old.method != "graphics" and method == "graphics"):
                figures[label] = fig

    for pno, para in body:
        sentences = _SENT_RX.split(para)
        for k, sent in enumerate(sentences):
            for m in REF_RX.finditer(sent):
                # the citing sentence plus one on each side: enough to say what the figure shows
                snippet = " ".join(sentences[max(0, k - 1):k + 2])[:700]
                for label in _expand(m["list"]):
                    fig = figures.get(label)
                    if fig and snippet not in fig.mentions and len(fig.mentions) < 8:
                        fig.mentions.append(snippet)

    return ParsedPdf(len(doc), title_guess, sorted(figures.values(), key=_sort_key))


def _expand(listing: str) -> list[str]:
    """'2 and 3' -> 2,3 ; '2-4' -> 2,3,4 ; '3(b)' -> 3 ; 'S1, S2' -> S1,S2"""
    nums = [(m.group(1), int(m.group(2)), m.end()) for m in _NUM_RX.finditer(listing)]
    out: list[str] = []
    for k, (pre, n, end) in enumerate(nums):
        out.append(f"{pre}{n}")
        if k + 1 < len(nums):
            between = listing[end:listing.find(str(nums[k + 1][1]), end)]
            if re.search(r"[\u2013-]|to", between) and not re.search(r"[a-z]\s*[\u2013-]", between):
                out.extend(f"{pre}{x}" for x in range(n + 1, min(nums[k + 1][1], n + 20)))
    return list(dict.fromkeys(out))


def _sort_key(f: Figure) -> tuple:
    m = re.fullmatch(r"([A-Z]*)(\d+)", f.label)
    return ({"": 0, "S": 1, "ED": 2}.get(m[1], 3), int(m[2])) if m else (9, 0)


def render(path: Path, page: int, bbox: list[float], max_px: int = 1600, margin: float = 6) -> bytes:
    """PNG of one region, at most max_px on its long side and at most 220 dpi."""
    doc = pymupdf.open(path)
    try:
        pg = doc[page - 1]
        clip = pymupdf.Rect(bbox[0] - margin, bbox[1] - margin, bbox[2] + margin, bbox[3] + margin) & pg.rect
        long_in = max(clip.width, clip.height) / 72
        dpi = max(72, min(220, int(max_px / long_in)))
        return pg.get_pixmap(dpi=dpi, clip=clip, alpha=False).tobytes("png")
    finally:
        doc.close()
