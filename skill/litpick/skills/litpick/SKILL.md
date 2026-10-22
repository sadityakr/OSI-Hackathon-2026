---
name: litpick
description: Open arXiv papers, list their figures, and look at a figure with a citation, through the local litpick library. Use when an analysis needs a published reference spectrum or plot, or a citation with a figure number. litpick does not search for papers; get the arXiv id from a literature search tool such as Valency Bond, or from your notes.
---

# litpick: open a paper, look at its figures

litpick parses arXiv PDFs and serves their figures. It does not search. Find papers with a separate literature search tool (for example Valency Bond), then bring the arXiv id here.

## With the litpick MCP tools (preferred)

1. `ingest_paper` with the arXiv id. A paper already in the library returns at once (`status` `cached`); a new one takes tens of seconds to a few minutes.
2. `list_figures` gives captions and the paragraphs that discuss each figure. Pick the one whose caption matches the material and conditions (laser, layer count, temperature).
3. `view_figure` with its printed number ("2", "Fig. 2") returns the image. Read peak positions off it (about +-1 cm-1) and say they were read from a figure.
4. `search_library` searches captions of papers already parsed, without network. Try it before asking for a new search.
5. Cite with `cite_as` from `view_figure`: author, year, arXiv id, figure number. Do not cite a paper you have not opened in this session as the source of a specific number.

## Without the MCP tools

The same operations as commands. Each prints one JSON object; `view` also saves a PNG in the current folder for you to read.

```
python "${CLAUDE_SKILL_DIR}/scripts/ib.py" ingest <arxiv_id>
python "${CLAUDE_SKILL_DIR}/scripts/ib.py" figures <arxiv_id>
python "${CLAUDE_SKILL_DIR}/scripts/ib.py" view <arxiv_id> "Fig. 2"
python "${CLAUDE_SKILL_DIR}/scripts/ib.py" library "<words>"
python "${CLAUDE_SKILL_DIR}/scripts/ib.py" status
```
