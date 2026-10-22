# Handover: the `lit-rag` skill (Oct 22, 2026)

Paste the block below into a fresh Claude Code session started on Aditya's computer in the repo folder
(`C:\Users\sadit\Desktop\P_Projects\Hackathons\OSI Hackathon`). The skill does not work from the cloud
session: it needs Aditya's SSH access to laufey.

---

You have a skill, `lit-rag`, that searches the AG Kläui group literature corpus and fetches paper
figures as local images. Use it for RamanLens work that needs published Raman literature: mode
assignments, polarization behaviour, reference spectra to compare against, and tracing a claim to its
source paper.

**What it is.** The corpus (about 10,800 parsed papers and theses: spintronics, 2D magnets, a useful
amount of Raman work, including CrSBr polarization-resolved Raman) lives on the GPU workstation
laufey in Lit-RAG, Aditya's RAG project. Lit-RAG serves its tools to KL Chat through an OpenAPI tool
server (Docker container `litrag-toolserver`, no published port). The skill reaches that server over
SSH: `scripts/litrag.py` pipes `scripts/remote_call.py` into `ssh laufey python3 -`, the helper reads
the access key and container address on laufey (the key never leaves laufey), calls the server, and
returns JSON. No MCP server, no local database, no local model.

**Files.** `C:\Users\sadit\.claude\skills\lit-rag\SKILL.md` (read it first), `scripts\litrag.py`
(local, Python 3.11, stdlib only), `scripts\remote_call.py` (runs on laufey's system Python 3.9,
stdlib only, so no 3.10+ syntax). The global `~/.claude` folder is an auto-committed git repo.

**Commands** (PowerShell, from the repo folder):

```powershell
python C:\Users\sadit\.claude\skills\lit-rag\scripts\litrag.py tools
python C:\Users\sadit\.claude\skills\lit-rag\scripts\litrag.py call search "@tmp\lit-rag\q.json"
python C:\Users\sadit\.claude\skills\lit-rag\scripts\litrag.py figures <citable_key> [<key> ...] --limit 8
```

- `tools`: the live, verbatim tool descriptions from the server's OpenAPI spec. Run once per session
  and follow them; they override any summary.
- `call <tool> @file.json`: write arguments to a JSON file with the Write tool (inline JSON quoting
  breaks in PowerShell). Example: `{"query": "Which Raman modes of CrSBr are observed and how do they
  depend on polarization?", "k": 5}`.
- `figures`: up to 5 papers per call; PNGs land in `tmp/lit-rag/<timestamp>/`. Open each `local_path`
  with the Read tool to actually see the plot.

**Allowed tools:** search, find_papers, get_paper, get_passage, follow_citation, graph_walk,
lookup_external, show_figures. `suggest_correction` (can hot-edit the group's live catalog) and
`suggest_add_paper` are refused on both sides. Do not work around that.

**Verified on Oct 22:** `tools` lists the 8 tools; semantic search on CrSBr polarization returned
Markina et al. 2026 (npj Quantum Mater. 11, 11) and Mondal et al. 2025 (npj 2D Mater Appl 9, 22) with
pages; `figures` downloaded Schilberth et al. 2026 Fig. 2 (polarized Raman of Co2Mo3O8) and it was
viewed; the write tool was refused.

**Search tips.** Semantic search is the default: ask full questions. To require a literal term, pass
`keywords` with every spelling (the parse splits subscripts, so `["MoS2", "MoS 2"]`). Hits carry
`figures_available`; batch those keys into one `figures` call. The server is rate-limited: keep `k` at
5 to 8.

**Rules for RamanLens.**
- Anything from the corpus is provenance class **literature**: cite from the hit's
  `citation_markdown` (drop its `/f/...` PDF links, they only resolve inside KL Chat).
- Before taking numbers for reference tables or relations, check the paper is not behind a held-out
  case (`data/test_set/README.md`, "Papers excluded from building tools": McDonnell 2018, Viner 2021,
  McDonnell 2020, Wdowik 2025).
- Developer aid only. Never wire it into `ramanlens.agent.toolset` or the `eval/run_agent.py` tools
  arm, and never use it in the public demo: it depends on laufey and private group PDFs, so judges
  cannot reproduce it.
- Figure crops and passages stay in `tmp/`. Never commit them.
- A non-`ok` status or empty result means the corpus does not hold it. Say so; never fill from memory.

**If it fails.** `ssh_error`: check `ssh laufey` works, then run the workstation-laufey health check.
`remote_error` mentioning docker: the container is down (`docker ps` on laufey; restarting it is
Aditya's call, it also serves KL Chat). `http_error 422`: wrong arguments, re-read `tools`. Do not edit
anything on laufey.

---
