# iopic-Bond

A local MCP server that wraps [Valency Bond](https://docs.valency.io/) and adds what Bond does not have. Bond finds papers; iopic-Bond downloads a paper's arXiv PDF, parses it into a graph of sections, paragraphs and figures, keeps every parse in a local library so no paper is parsed twice, and hands figures to the model so it can look at them.

Everything runs on your machine with your own Valency token. Nothing is hosted, and parsed papers stay in your library folder. Design and rationale: `docs/iopic-bond.md` in the RamanLens repo.

## Status (Oct 22, 2026)

| Part | State |
|---|---|
| arXiv fetch, Docling parse, parse-once library, `ingest_paper`, `list_figures`, `view_figure`, `search_library`, `library_status` | verified: arXiv 1005.2509 ingested (cold 2 min 57 s on CPU including the first model download, cached 3.3 s), 3 offline tests pass including a real MCP client |
| `find_papers`, `expand` (Bond calls) | written, not yet run: needs `VALENCY_BOND_TOKEN` |
| LangSmith spans, `iopic-bond warmup`, `serve --http` | written, not yet run |
| Use from Claude Desktop and Claude Code | not yet tried |
| `show_figures` panel that shows figures to you (MCP Apps) | not built |

## Install

```
pip install -e "iopic-bond[parse]"     # [parse] adds Docling (PyTorch); omit it for search only
iopic-bond warmup                       # one-time Docling model download
iopic-bond doctor                       # checks library folder, token, Bond connection, parser, tracing
```

Settings come from the environment, or from a `.env` file found from the current working directory upward (or the file named by `IOPIC_BOND_ENV_FILE`):

| Variable | Meaning |
|---|---|
| `VALENCY_BOND_TOKEN` | Valency Direct API bearer token, from the Settings page in the Valency app; see https://docs.valency.io/guides/api/ |
| `IOPIC_BOND_HOME` | library folder (default: the OS cache dir, e.g. `%LOCALAPPDATA%\iopic-bond` on Windows) |
| `IOPIC_BOND_DEVICE` | `auto` (default: cuda when a GPU is visible, otherwise cpu), `cpu`, or `cuda` |
| `IOPIC_BOND_SEARCH` | `on` (default) also serves `find_papers` and `expand` through Valency Bond; `off` serves only the parse and figure tools (the litpick plugin in `skill/litpick/`) |
| `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` | optional tracing; `LANGSMITH_PROJECT` defaults to `iopic-bond` |

Chat clients such as Claude Code connect to Bond itself with a browser sign-in; iopic-Bond is a program calling Bond, which is the case Valency's Direct API token is for.

## Use from Claude Code

Registered for your machine only, so your paths stay out of the repo:

```
claude mcp add iopic-bond --scope local -e IOPIC_BOND_HOME="C:/path/to/library" -- "C:/path/to/.venv/Scripts/iopic-bond.exe" serve
```

Claude Code starts the server in the project folder, so a `.env` there is found.

## Use from Claude Desktop

Claude Desktop starts the server outside your project, so `.env` is not found: put the token in the `env` block of `claude_desktop_config.json`.

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
| `find_papers` | concept search through Bond; arXiv and journal records of one paper merged, arXiv kept; says whether each paper can be parsed and whether it is already in the library |
| `expand` | papers citing an anchor paper (`mode="citing"`), or similar papers (`mode="similar"`) |
| `ingest_paper` | download and parse an arXiv paper, or return the stored parse; returns section outline and figure list |
| `list_figures` | figures of a parsed paper with captions, page, and the paragraphs that discuss them |
| `view_figure` | the figure image itself plus its caption, for the model to look at |
| `search_library` | full-text search over captions, discussing paragraphs and titles of every parsed paper; offline |
| `library_status` | what is in the library and where it is |

Query Bond by concept ("Raman mode assignment in CrSBr"), never by peak positions: its search is embedding based and does not encode numbers.

Naming a figure in `view_figure`: its printed number (`"2"`, `"Fig. 2"`, `"Figure 2"`). Images without a caption (for example a table-of-contents graphic) are listed as `image N (no caption)` and named `"image N"`; they never get a figure number, because the crop order is not the paper's numbering.

Every result carries a `status` (`ok`, `cached`, `not_ingested`, `not_found`, `fetch_failed`, `parse_failed`, `bond_error`, ...), so a missing paper is reported, not raised.

## Command line

| Command | What it does |
|---|---|
| `iopic-bond serve` | run the MCP server over stdio (what clients launch) |
| `iopic-bond serve --http --port 8765` | Streamable HTTP instead (not yet tested) |
| `iopic-bond ingest <arxiv_id> [--force]` | ingest one paper without a client |
| `iopic-bond reindex` | rebuild `index.sqlite` from the paper folders |
| `iopic-bond doctor`, `iopic-bond warmup` | see Install |

## Library layout

```
<IOPIC_BOND_HOME>/
  index.sqlite                       derived; rebuildable with `iopic-bond reindex`
  papers/<arxiv_id>/paper.pdf
  papers/<arxiv_id>/meta.json        Bond record, content hash, parser version
  papers/<arxiv_id>/parsed/<hash>/   tree.json (the graph), text.txt, paper.md, figures/
  bond/                              cached Bond responses (7 days)
```

A paper is re-parsed only when the parser version changes or `--force` is given.

## Tests

```
pytest iopic-bond/tests -q
```

The MCP client test runs only when `IOPIC_BOND_HOME` points at a library that contains arXiv 1005.2509 (`iopic-bond ingest 1005.2509` once); otherwise it is skipped.

## Next steps

In order; each ends with something that can be shown.

1. **Bond calls.** Put `VALENCY_BOND_TOKEN` in `.env`, run `iopic-bond doctor` (expect `bond ok`), then call `find_papers` and `expand` once each. If the Settings page offers no token, add browser sign-in instead: `OAuthClientProvider` from the `mcp` SDK against `https://oauth.valency.io` (dynamic client registration is offered), as an `iopic-bond login` command; only `bond.py` changes.
2. **Retrieval test.** The 10 material-property pairs from `docs/bond-evaluation.md`; target: the known reference paper in the top 5 for 8 of 10. Keep the query wording that works.
3. **Client run.** Register in Claude Code, run find, ingest, view on one MoS2 paper; then the same in Claude Desktop. Check that the model describes the figure correctly and cites it as "Fig. N of arXiv:id".
4. **Tracing.** With LangSmith keys set, confirm one trace with nested `iopic.*`, `bond.call`, `figure.fetch`, `figure.parse` spans.
5. **`show_figures` panel** for Claude Desktop (the demo client): an MCP Apps `ui://` resource (`mcp.server.apps` in the SDK) showing figures with their citation. First test whether the panel may show images embedded as data URIs; if not, fall back to file paths.
6. **Wire into RamanLens** (build loop task T10): the agent toolset calls `iopic_bond.library` directly so evaluation runs are traced end to end.
7. **Warm-parse timing** on GPU (`IOPIC_BOND_DEVICE=cuda`) and on a longer paper, so the demo does not stall on a cold parse.
8. **After the hackathon:** CC BY filter on Bond's `license` field for anything shown publicly, `serve --http` for ChatGPT (needs public HTTPS and OAuth on our side), and splitting `iopic-bond/` into its own repository.

## Licence

Code: MIT. Papers and figures in your library remain under their authors' licences (most arXiv papers carry the arXiv non-exclusive distribution licence); do not republish them, and keep the library folder out of version control.
