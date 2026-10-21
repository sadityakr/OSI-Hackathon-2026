# ramanlens

## 60-second quickstart (will fill in as modules land)

```
cd "OSI Hackathon"
python -m venv .venv && .venv\Scripts\activate       # Windows
pip install -e src[trace]                              # or: pip install -e src
copy .env.example .env                                 # add keys
```

Tracing (optional, recommended): set in `.env`

```
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=ramanlens
ANTHROPIC_API_KEY=...
```

Without `LANGSMITH_API_KEY` every tool runs untraced. With it, each analysis is one
trace tree (see `ramanlens/tracing.py` for the span names) and the trace URL is written
into the report JSON.

Smoke test:

```
python -c "from ramanlens.tracing import traced, tracing_enabled; print(tracing_enabled())"
```

## Layout

- `ramanlens/tracing.py` LangSmith decorator, root-run context, wrapped Anthropic client.
- `ramanlens/perception/` readers, preprocessing, peak fitting, CRD matcher, group theory.
- `ramanlens/relations/` cited physics relations, one module per material family.
- `ramanlens/literature/` Bond client, PDF parsing, figure extraction, panel selection, digitizer, cache.
- `ramanlens/agent/` runner (Anthropic SDK plus tools, fully traced) and the Claude Code tool manifest.
