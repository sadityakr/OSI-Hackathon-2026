# iopic-Bond

A local MCP server that wraps [Valency Bond](https://docs.valency.io/) and adds what Bond does not have: it downloads a paper's arXiv PDF, parses it into a graph of sections, paragraphs and figures, keeps every parse in a local library, and shows the figures to the model and to you.

Everything runs on your machine with your own Valency token. Nothing is hosted, and parsed papers stay in your library folder.

## Install

```
pip install -e "iopic-bond[parse]"     # [parse] adds Docling (PyTorch); omit it for search only
iopic-bond warmup                       # one-time model download
iopic-bond doctor                       # checks library folder, token, parser
```

Settings (environment or a `.env` file in the working directory):

| Variable | Meaning |
|---|---|
| `VALENCY_BOND_TOKEN` | Direct API token from https://app.valency.io/settings |
| `IOPIC_BOND_HOME` | library folder (default: the OS cache dir) |
| `IOPIC_BOND_DEVICE` | `cpu` (default) or `cuda` for Docling |
| `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` | optional tracing |

## Use from Claude Desktop or Claude Code

```json
{
  "mcpServers": {
    "iopic-bond": {
      "command": "C:/path/to/.venv/Scripts/iopic-bond.exe",
      "args": ["serve"],
      "env": { "IOPIC_BOND_HOME": "C:/path/to/library", "VALENCY_BOND_TOKEN": "..." }
    }
  }
}
```

## Tools

| Tool | What it does |
|---|---|
| `find_papers` | concept search through Bond, duplicates merged, arXiv preferred |
| `expand` | papers citing an anchor paper, or similar papers |
| `ingest_paper` | download and parse an arXiv paper, or return the stored parse |
| `list_figures` | figures of a parsed paper with captions and the paragraphs that discuss them |
| `view_figure` | the figure image itself, for the model to look at |
| `search_library` | full-text search over captions of every parsed paper, offline |
| `library_status` | what is in the library |

## Library layout

```
<IOPIC_BOND_HOME>/
  index.sqlite                       rebuildable with `iopic-bond reindex`
  papers/<arxiv_id>/paper.pdf
  papers/<arxiv_id>/meta.json        Bond record, content hash, parser version
  papers/<arxiv_id>/parsed/<hash>/   tree.json (the graph), paper.md, figures/
  bond/                              cached Bond responses (7 days)
```

## Licence

Code: MIT. Papers and figures in your library remain under their authors' licences (most arXiv papers: arXiv non-exclusive distribution licence); do not republish them.
