# Evaluation: bare agent vs agent with RamanLens tools

The results in the write-up come from `run_claude_code.py` (headless Claude Code, arms `bare` and `skill`, no API
key needed), `baselines.py` (non-LLM arms `libsearch` and `pipeline`), `score.py` (identification) and `judge.py`
(blind rubric judge for interpretation). Commands are in the repository README. The section below describes the
first runner, `run_agent.py`, which drives the same comparison through the Anthropic SDK.

Same model (`claude-opus-5-5`, adaptive thinking, same effort), same system prompt, same Python sandbox. The only
difference between the arms is the tool list:

| Arm | Tools |
|---|---|
| `bare` | `run_python` (numpy, scipy, pandas, lmfit, matplotlib; the `ramanlens` package is blocked), `submit_report` |
| `tools` | the same, plus the domain tools from `ramanlens.agent.toolset` (fitter, CRD and literature matcher, polarization classifier, reference tables, relations) |

Both arms end by calling `submit_report` with the schema in `report_schema.py`; `score.py` compares the report to
`truth.json`.

## Commands (from the repo root)

```powershell
# regenerate the synthetic tier (deterministic; needs data/raw/crd/crd_2d.pkl or crd.json)
.venv\Scripts\python.exe eval\synth\make_synthetic.py --crd data\raw\crd\crd_2d.pkl

# smoke run first: two cases per arm, to measure cost (tokens are in each transcript.json under "usage")
.venv\Scripts\python.exe eval\run_agent.py --arm bare  --split dev --cases syn-WS2-01 syn-GeS-02 --run-name smoke
.venv\Scripts\python.exe eval\run_agent.py --arm tools --split dev --cases syn-WS2-01 syn-GeS-02 --run-name smoke
.venv\Scripts\python.exe eval\score.py eval\runs\smoke

# the headline comparison (held-out split), only after the tools arm is built
.venv\Scripts\python.exe eval\run_agent.py --arm bare  --split heldout --run-name final
.venv\Scripts\python.exe eval\run_agent.py --arm tools --split heldout --run-name final
.venv\Scripts\python.exe eval\score.py eval\runs\final
```

Needs `ANTHROPIC_API_KEY` in `.env`. Model calls are traced to LangSmith when `LANGSMITH_TRACING=true` and a key are set.

## Metrics

`id_top1`, `id_top3` (identify cases, material matched by element counts), `hint_correct` (verify cases, including
deliberately wrong hints), `peak_recall`, `peak_precision`, `position_mae_cm1`, `irrep_acc`, `pattern_acc`
(angle series), `cosmic_ray_rejected`. `leak_suspects` lists cases whose transcript mentions truth files.

## Fairness notes

- The bare arm can still write any analysis code; it only lacks domain data and domain tools. This isolates the
  value of the tools, not of code execution.
- Synthetic cases come from the CRD, which the tools arm's matcher also uses, so identification on them flatters
  the tools arm. Report synthetic and experimental (`exp-*`) cases separately.
- No server-side model fallback is enabled: a refusal fallback would silently mix models within an arm.
