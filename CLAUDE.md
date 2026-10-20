# OSI Hackathon 2026 project

Working repo for Aditya's participation in the 4th Open Scientific Intelligence Hackathon (Oct 21 to 22, 2026). Read this file first in every session.

## Hard constraints

- **Deadline: Fri Oct 23, 02:00 CEST** (Thu Oct 22, 7 pm CT). Everything must be submitted by then.
- Deliverables: (1) public post with a video up to 4 min, no voice speed-up; (2) one-page write-up with a figure; (3) public code/data link; (4) submission form.
- Judging: potential for impact, innovativeness, relevance to physical sciences/math, novelty. Optimize for these, not polish.
- Organizer mindset: speed over polish, learning over perfection, collaboration over silos. Scope ambitiously ("two days to a real discovery").

## Phases

1. **Brainstorm** (now, Oct 20): collect and rank ideas in `ideas/`. Decide on one concept and roles before kickoff.
2. **Build** (Oct 21 to 22): working prototype in `src/`, data in `data/`, exploration in `notebooks/`.
3. **Submit** (Oct 22 evening CEST): one-pager, figure and video script in `submission/`.

## Folder layout

- `resources/` event info, Slack announcements, judging criteria, Miro pitches of interest, sponsor details. Reference only, do not edit except to add new intel.
- `ideas/` one markdown file per candidate idea, plus `ranking.md` once we compare them.
- `src/` code. Python 3.11+, keep it runnable with `uv` or plain `pip`. One `README.md` with a 60-second quickstart.
- `data/` raw and processed data. Large files are gitignored; keep a `data/README.md` describing where each dataset came from.
- `notebooks/` exploratory work. Consider Marimo notebooks (sponsor prize) over Jupyter.
- `submission/` one-pager draft, figure, video script and shot list, links.

## About Aditya (context for idea selection)

- PhD candidate in experimental condensed-matter physics (AG Kläui, JGU Mainz): TMR in van der Waals heterostructures, exchange bias, thin-film growth, cryogenic transport, Raman/characterization of 2D materials.
- Leads the group's AI task force: agentic RAG over literature and an internal wiki, LLM-driven instrumentation (CryoSoft), scientific data extraction (TracEx).
- Strong fit areas: lab automation and instrument control, spectroscopy and transport data pipelines, 2D magnetic materials, agentic literature tools.

## Working conventions

- Prefer small, verifiable steps; every claim in the write-up must be reproducible from `src/`.
- Prefer open data (RRUFF, Materials Project, OQMD, HF datasets, awesome-matchem-datasets) and record provenance in `data/README.md`.
- Sponsor tracks worth a cheap integration if natural: Valency MCP Bond (literature citations), Marimo (notebooks), Adaption (credits). Do not contort the project for them.
- No em dashes in any written output.
- Keep a running `LOG.md` at the root with dated bullets of decisions and progress so the final write-up and video script can be assembled quickly.

## Useful links

- Submissions archive (120+ past projects): https://llmhackathon.github.io/submissions
- Datasets: https://github.com/blaiszik/awesome-matchem-datasets
- Miro teaming board: https://miro.com/app/board/uXjVEeJogfE=/?share_link_id=927837268598
- Luma registration: https://luma.com/ku88xh92
- Full event notes: `resources/event-info.md`
