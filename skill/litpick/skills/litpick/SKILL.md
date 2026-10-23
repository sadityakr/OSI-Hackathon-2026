---
name: litpick
description: Open arXiv papers or local PDFs, list their figures, and look at a figure with a citation, through the local litpick library. Use when an analysis needs a published reference plot or spectrum, or a citation with a figure number. litpick does not search for papers; get the arXiv id from a literature search tool such as Valency, or from your notes.
---

# litpick: open a paper, look at its figures

litpick downloads arXiv PDFs (or takes a PDF on this computer), finds every figure with its caption,
and keeps them in a library on this computer. It does not search for papers. Find papers with a
literature search tool first, then bring the arXiv id here.

## With the litpick MCP tools (preferred)

1. `search_library` first: it searches captions of papers already opened, offline. If a figure there
   fits, skip to step 4.
2. `ingest_paper` with the arXiv id, an arXiv URL, or the full path of a PDF. A paper already in the
   library returns at once (`status` `cached`); a new one takes a few seconds to a minute.
3. `list_figures` gives every caption and the sentences that discuss each figure. Pick the one whose
   caption matches what you need (material, layer count, temperature, field direction).
4. `view_figure` with the printed number ("2", "Fig. 2", "S1") returns the image. If its `region` is
   `gap` or `page`, the crop may be loose; say so. Values read off a plot are approximate: say they
   were read from the figure and give the precision you can actually read.
5. Cite with the `cite_as` string from `view_figure`. Do not cite a paper as the source of a number
   unless you opened that figure in this session.

## Without the MCP tools

The same operations on the command line. Each prints one JSON object; `view` also saves a PNG in the
`--out` folder for you to read.

```
uvx --from "${CLAUDE_PLUGIN_ROOT}" litpick search "CrSBr magnetoresistance"
uvx --from "${CLAUDE_PLUGIN_ROOT}" litpick ingest 2407.13230
uvx --from "${CLAUDE_PLUGIN_ROOT}" litpick figures 2407.13230
uvx --from "${CLAUDE_PLUGIN_ROOT}" litpick view 2407.13230 "Fig. 2" --out .
uvx --from "${CLAUDE_PLUGIN_ROOT}" litpick status
```

If `${CLAUDE_PLUGIN_ROOT}` is not set in the shell, use the folder two levels above this file.

## When something fails

- `could not reach arXiv`: this environment cannot reach arxiv.org. Ask the person to attach the
  PDF, then `ingest_paper` its path.
- `is not in the library yet`: run `ingest_paper` first.
- `has no figure 'X'. It has: ...`: use one of the listed numbers.
