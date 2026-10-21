# iopic-Bond: a local MCP server that turns Bond search results into parsed paper graphs and figures

Date: 2026-10-21. Status: design agreed, step 1 and 2 in build. Code: `iopic-bond/`.

## What iopic-Bond does

Valency Bond finds papers (search, DOI, citation graph) but returns no full text and no figures. iopic-Bond wraps Bond and adds everything after "which paper":

```
Bond search / citations
  -> arXiv PDF download
  -> Docling parse into a BlockNode graph (tree.json: sections, paragraphs, figures,
     containment edges, "Fig. N" reference edges)
  -> figures with captions and the paragraphs that mention them
  -> figures shown to the person (MCP Apps panel) and to the model (image content)
```

Each parsed paper is kept, so the library grows with use and a paper is never parsed twice.

## Why it runs on each user's machine and is not hosted

iopic-Bond is an open-source package that each user installs and that their MCP client (Claude Desktop, Claude Code, VS Code) launches as a local stdio process. Everything executes on the user's machine:

| Step | Runs on | Uses |
|---|---|---|
| Bond calls | user's machine, to `https://mcp.valency.io/` | the user's own Valency API token |
| arXiv PDF download | user's machine | user's network |
| Docling parse, figure crops | user's machine | user's CPU or GPU |
| Library of parsed papers | user's disk | per user |
| LangSmith tracing | user's machine | optional, user's own key |

A hosted service would need storage, GPU time for parsing, sign-in for every user, protection of a shared Valency token, and it would redistribute paper figures. Running locally removes all five. The same code can run in Streamable HTTP mode on a machine a group controls (a launch flag, not a second codebase).

Bond authentication uses the Direct API bearer token from `https://app.valency.io/settings` (documented at https://docs.valency.io/guides/api/), read from `VALENCY_BOND_TOKEN`. Bond's OAuth with dynamic client registration also exists (`https://oauth.valency.io/register`) and is the fallback if per-user browser sign-in is ever needed.

## Where data is stored: one folder per paper plus a SQLite index

Root: `IOPIC_BOND_HOME` if set, else the OS cache directory from `platformdirs` (Windows `%LOCALAPPDATA%\iopic-bond`, macOS `~/Library/Caches/iopic-bond`, Linux `~/.cache/iopic-bond`). For the hackathon it points at `data/raw/iopic-bond/` (gitignored).

```
<IOPIC_BOND_HOME>/
  index.sqlite                  index over the folders; rebuildable with `iopic-bond reindex`
  papers/<arxiv_base_id>/
    paper.pdf
    meta.json                   Bond record (title, DOI, licence, citations) + content hash + parser version
    parsed/<content_hash>/      parser output, unchanged from the pipeline
      tree.json                 the graph, single source of truth
      text.txt, paper.md
      figures/figN.png, figN.md
  bond/<query_hash>.json        cached Bond responses
```

Files are the truth; `index.sqlite` is a derived index. SQLite ships with Python (no install), and its FTS5 full-text search (verified present, SQLite 3.50.4) indexes figure captions across the whole library.

Parse-once rule: before parsing, look up by DOI, then by arXiv base id (Bond returns `doi: ""` for some arXiv records). If a parse exists with the current parser version, return it. If the parser version changed, re-parse. Otherwise fetch, parse, index.

All storage goes through `store.py`, so a remote store could be added later without touching the tools.

## Why there is no shared hosted database

A shared database of parsed graphs (for example the group's Postgres) was considered and dropped for now. It would bring back the hosted-service problems: write authentication, trust in other users' parses, and redistribution of full text and figure crops. Most arXiv papers carry `LicenseRef-arXiv-nonexclusive-distrib-1.0`, which grants arXiv a distribution right and gives third parties no right to republish (moderate confidence; not legal advice). Two safe future versions: a metadata-only index ("this DOI is parsed, 4 figures"), or full content restricted to CC BY papers using Bond's `license` field.

## Tools

| Tool | Purpose | Source |
|---|---|---|
| `find_papers(query, limit)` | concept search; duplicates merged on DOI or arXiv id, arXiv preferred; each result says whether it is already in the library | Bond `semantic_search_papers` |
| `expand(paper_id, mode)` | papers that cite it, or similar papers | Bond `get_citing_papers`, `find_similar_papers` |
| `ingest_paper(arxiv_id)` | fetch and parse, or return the cached parse; returns sections and figure list | arXiv, Docling |
| `list_figures(arxiv_id)` | labels, captions, page, mentioning paragraphs | `tree.json` |
| `view_figure(arxiv_id, figure)` | the figure image itself plus caption, so the model can look at it | MCP image content |
| `search_library(query)` | full-text search over captions of every parsed paper; no network | `index.sqlite` |
| `show_figures(arxiv_id, figures)` | MCP Apps panel that shows figures with citations to the person | `ui://` resource |

Every result carries an explicit `status` (`ok`, `not_found`, `not_on_arxiv`, `parse_failed`, ...): a missing paper is data the agent reasons about, not an exception.

Query rule from `docs/bond-evaluation.md`: concept queries only, never peak frequencies.

## How figures reach the model and the person

Client behaviour (research of 2026-10-21; sources in the session log):

| Client | Model sees image content | Person sees it |
|---|---|---|
| Claude Code | yes (code.claude.com/docs/en/mcp) | not documented |
| Claude Desktop, claude.ai | yes | collapsed in the tool block; MCP Apps panels render |
| ChatGPT | reportedly not | MCP Apps panels only, needs public HTTPS |

So: `view_figure` returns image content for the model; `show_figures` renders an MCP Apps panel with the PNG embedded as a data URI, so no image web server is needed for a local install; every result also carries the file path. Demo client: Claude Desktop.

## Licence stance for the deliverable

Figures are downloaded and cropped on the user's machine from the user's own arXiv download, shown with a full citation, and never committed. The cache lives under `data/raw/` (gitignored). For the public video, prefer papers whose Bond `license` is CC BY.

## Install and configuration

```
uv pip install -e iopic-bond[parse,trace]
iopic-bond warmup          # one-time Docling model download, so the first parse does not time out in the client
```

Claude Desktop (`claude_desktop_config.json`) or Claude Code (`.mcp.json`):

```json
{
  "mcpServers": {
    "iopic-bond": {
      "command": "<repo>/.venv/Scripts/iopic-bond.exe",
      "args": ["serve"],
      "env": { "IOPIC_BOND_HOME": "<repo>/data/raw/iopic-bond" }
    }
  }
}
```

`VALENCY_BOND_TOKEN` (and optional LangSmith keys) are read from the environment or a `.env` file in the working directory.

## Tracing

Every tool is a LangSmith span (`iopic.<tool>`, with `bond.<tool>`, `figure.fetch`, `figure.parse` nested inside) when `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` are set. Because the server is a Python process, its spans reach LangSmith even when Claude Code or Claude Desktop drives it; only the client's own model calls stay invisible.

## Build order

1. Bond client, `find_papers`, `expand`; retrieval test from `docs/bond-evaluation.md`.
2. Store, `ingest_paper`, `list_figures`, `view_figure`, `search_library` over stdio; end to end on Lee et al. 2010 (arXiv 1005.2509).
3. `show_figures` MCP Apps panel, verified in Claude Desktop.
4. Streamable HTTP mode and ChatGPT, if time allows.
