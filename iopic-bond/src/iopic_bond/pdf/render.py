"""Render a ``BlockNode`` tree to ``paper.md`` — the Obsidian-style Markdown vault view.

This is a **derived projection** of ``tree.json`` (design §3 step 6), for human reading and parse-QA:
a person (or a Haiku reviewer) opens the vault folder in Obsidian and eyeballs whether structure,
equations, and figures survived the parse. ``tree.json`` is truth; this is a view of it.

Vault conventions (chosen so it renders in Obsidian *and* is deterministically checkable by
``qa.py``):

* figures use Obsidian embeds — ``![[figures/figN.png]]`` — so they show inline when the per-paper
  folder is opened as a vault; ``qa.py`` checks every embed target exists on disk.
* equations are ``$$ … $$`` blocks carrying the LaTeX from the ``equation`` node's ``attrs``.
* headings nest by the node's container depth (clamped to H1–H6).
* the document root's citable identity becomes YAML frontmatter.
"""

from __future__ import annotations

from .schema import BlockNode


def figure_note_rel(image_path: str) -> str:
    """Vault-relative path of a figure's note, derived from its image path.

    ``figures/fig3.png`` -> ``figures/fig3.md``. The figure note (image + caption + a VLM-description
    slot) is the per-figure embeddable unit; ``paper.md`` transcludes it via this path.
    """
    stem = image_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return f"figures/{stem}.md"


# Front-matter keys lifted from the root node's attrs, in display order.
_FRONTMATTER_KEYS = (
    "title",
    "authors",
    "journal",
    "year",
    "published_date",
    "volume",
    "issue",
    "pages",
    "doi",
    "citable_key",
)


def _yaml_scalar(value) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(_yaml_scalar(v) for v in value) + "]"
    s = str(value)
    if any(c in s for c in ':#[]{}"\n') or s == "":
        return '"' + s.replace('"', '\\"') + '"'
    return s


def _frontmatter(root: BlockNode) -> list[str]:
    lines = ["---"]
    for key in _FRONTMATTER_KEYS:
        if key in root.attrs and root.attrs[key] not in (None, "", []):
            lines.append(f"{key}: {_yaml_scalar(root.attrs[key])}")
    lines.append(f"n_pages: {root.attrs.get('n_pages', '?')}")
    lines.append("---")
    return lines


def _table_md(node: BlockNode) -> list[str]:
    """Render ``attrs['cells']`` (list of row-lists of strings) as a GitHub Markdown table."""
    cells = node.attrs.get("cells")
    if not cells:
        return ["*(table — structure not captured)*"]
    out = []
    header = cells[0]
    out.append("| " + " | ".join(str(c).replace("|", "\\|") for c in header) + " |")
    out.append("| " + " | ".join("---" for _ in header) + " |")
    for row in cells[1:]:
        out.append("| " + " | ".join(str(c).replace("|", "\\|") for c in row) + " |")
    return out


def _render_node(node: BlockNode, heading_level: int, out: list[str]) -> None:
    t = node.type

    if t in ("chapter", "section", "subsection"):
        level = min(heading_level, 6)
        title = (node.text or node.attrs.get("label") or t).strip()
        out.append(f"{'#' * level} {title}")
        out.append("")
        for child in node.children:
            _render_node(child, heading_level + 1, out)
        return

    if t in (
        "author",
        "affiliation",
        "funding",
        "acknowledgement",
        "supplementary-material",
        "data-availability",
    ):
        # front/back-matter containers: a light heading + their content
        if node.text:
            out.append(f"{'#' * min(heading_level, 6)} {t.replace('-', ' ').title()}")
            out.append("")
            out.append(node.text)
            out.append("")
        for child in node.children:
            _render_node(child, heading_level + 1, out)
        return

    if t == "paragraph":
        if node.text:
            out.append(node.text)
            out.append("")
    elif t == "abstract":
        if node.text:
            out.append("**Abstract.** " + node.text)
            out.append("")
    elif t == "figure":
        # transclude the figure's own note (image + caption + VLM-description slot) so each figure is
        # one self-contained, embeddable unit; the note renders inline here via the Obsidian embed.
        note = node.attrs.get("note_path")
        img = node.attrs.get("image_path")
        if note:
            out.append(f"![[{note}]]")
        elif img:
            out.append(f"![[{img}]]")
        else:
            out.append(f"*(figure {node.attrs.get('label', '')} — image not extracted)*")
        out.append("")
    elif t == "caption":
        # standalone captions already shown with their figure (caption-of edge) are skipped to
        # avoid duplication; an unlinked caption still renders in flow.
        if node.text and not any(e.type == "caption-of" for e in node.edges):
            out.append(f"*{node.text.strip()}*")
            out.append("")
    elif t == "equation":
        latex = (node.attrs.get("latex") or node.text or "").strip()
        if latex:
            out.append("$$")
            out.append(latex)
            out.append("$$")
        else:
            # no LaTeX (e.g. formula enrichment disabled) — placeholder, not an empty $$ block
            out.append("*(equation — not captured)*")
        out.append("")
    elif t == "table":
        if node.attrs.get("label"):
            out.append(f"**{node.attrs['label']}**")
            out.append("")
        out.extend(_table_md(node))
        out.append("")
    elif t in ("list", "list-item"):
        if node.text:
            out.append(f"- {node.text.strip()}")
        for child in node.children:
            _render_node(child, heading_level, out)
        if t == "list":
            out.append("")
    elif t == "footnote":
        if node.text:
            out.append(f"> [!note] footnote\n> {node.text.strip()}")
            out.append("")
    elif t == "reference":
        if node.text:
            out.append(f"- {node.text.strip()}")
    else:
        if node.text:
            out.append(node.text)
            out.append("")

    for child in node.children:
        _render_node(child, heading_level, out)


def render_markdown(root: BlockNode) -> str:
    """Return the full ``paper.md`` text for a parsed document root."""
    out: list[str] = []
    out.extend(_frontmatter(root))
    out.append("")
    title = root.attrs.get("title", "Untitled")
    out.append(f"# {title}")
    out.append("")
    for child in root.children:
        _render_node(child, heading_level=2, out=out)
    # collapse 3+ blank lines to a single blank line
    text = "\n".join(out)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.rstrip() + "\n"
