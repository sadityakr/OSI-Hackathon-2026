"""Run one agent arm over test-set cases and save each report and transcript for scoring.

This produces the headline comparison of the project: the same model, prompt skeleton and Python sandbox, with
and without the RamanLens domain tools. The arms differ only in the tool list, so any score difference is the
value of the tools.

Input:
    data/test_set/<split>/<case_id>/{input.json, spectrum.csv}. truth.json is never read or copied.
    Arm "bare": tools run_python + submit_report; the ramanlens package is blocked inside run_python.
    Arm "tools": the same, plus the domain tools exported by ramanlens.agent.toolset (TOOLS, call).
    ANTHROPIC_API_KEY (or another credential the Anthropic SDK resolves) from the environment or .env.
Process:
    For each case: copy the spectrum into a fresh work folder, send the case prompt, run the manual tool-use loop
    until submit_report is called or the turn limit is hit. Model calls go through ramanlens.tracing so they appear
    in LangSmith when tracing is configured. Adaptive thinking; effort set explicitly; no model fallback, so each
    arm is scored on one model only.
Output:
    eval/runs/<run_name>/<arm>/<case_id>/{report.json, transcript.json, work/}. Score with eval/score.py.
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
from report_schema import SUBMIT_TOOL  # noqa: E402

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

MODEL = "claude-opus-5-5"

SYSTEM = """You are analysing a Raman spectroscopy measurement of a layered (van der Waals) material.
Work in the current folder only: the data file is ./spectrum.csv. Do not read files outside this folder.
Use the tools to inspect and analyse the data quantitatively. Then call submit_report exactly once.

Reporting rules:
- Every peak carries a provenance: measured (from the fit), inferred (your reasoning), literature (a reference).
  Give a source for every assignment that is not purely measured.
- Report substrate lines (for example Si at 520.7 cm-1) as peaks with assignment 'Si substrate'.
- Do not report cosmic-ray spikes as peaks; list them under artifacts.
- For angle-resolved data classify each peak's polarization dependence with one of:
  isotropic_par_only (parallel constant, crossed zero), isotropic_both (parallel and crossed constant and equal),
  twofold (180 degree period), fourfold (cos^2(2 theta) in parallel, sin^2(2 theta) in crossed), silent, other.
- For a verify task, judge whether the spectrum is consistent with the stated material and say why.
- State what the data cannot tell you under limits. Say so when you are unsure rather than guessing."""

BLOCK_RAMANLENS = "import sys as _s; _s.modules['ramanlens'] = None  # bare arm: domain package blocked\n"

RUN_PYTHON = {
    "name": "run_python",
    "description": "Run a Python 3 script in the case work folder and return stdout and stderr (truncated to "
                   "12000 characters). numpy, scipy, pandas, lmfit and matplotlib are available. Each call is a "
                   "fresh process: save intermediate results to files if you need them later. Timeout 180 s.",
    "input_schema": {"type": "object", "additionalProperties": False, "required": ["code"],
                     "properties": {"code": {"type": "string"}}},
}


def run_python(code, workdir, arm):
    script = workdir / "_cell.py"
    script.write_text((BLOCK_RAMANLENS if arm == "bare" else "") + code, encoding="utf-8")
    try:
        p = subprocess.run([sys.executable, script.name], cwd=workdir, capture_output=True, text=True,
                           timeout=180, encoding="utf-8", errors="replace")
        out = (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.stderr else "")
    except subprocess.TimeoutExpired:
        out = "[timeout after 180 s]"
    return out[-12000:] if len(out) > 12000 else (out or "[no output]")


def load_toolset(arm):
    if arm == "bare":
        return [], None
    from ramanlens.agent import toolset  # built by the loop; contract in tests/contract/test_toolset.py
    return list(toolset.TOOLS), toolset.call


def case_prompt(inp):
    meta = {k: v for k, v in inp.items() if k not in ("case_id", "question")}
    return (f"{inp['question']}\n\nMeasurement metadata:\n{json.dumps(meta, indent=2)}\n\n"
            "The data is in ./spectrum.csv. "
            + ("Columns: shift_cm1,intensity,angle_deg,config (config is parallel or crossed)."
               if inp["kind"] == "angle_series" else "Columns: shift_cm1,intensity."))


def block_to_dict(b):
    return b.model_dump(exclude_none=True) if hasattr(b, "model_dump") else dict(b)


def run_case(client, case_dir, out_dir, arm, effort, max_turns):
    inp = json.loads((case_dir / "input.json").read_text())
    work = out_dir / "work"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    work.mkdir(parents=True)
    shutil.copy(case_dir / "spectrum.csv", work / "spectrum.csv")
    domain_tools, call = load_toolset(arm)
    tools = [RUN_PYTHON] + domain_tools + [SUBMIT_TOOL]
    messages = [{"role": "user", "content": case_prompt(inp)}]
    report, usage, t0 = None, {"input": 0, "output": 0, "tool_calls": 0}, time.time()
    for _ in range(max_turns):
        resp = client.messages.create(model=MODEL, max_tokens=16000, system=SYSTEM, tools=tools,
                                      messages=messages, thinking={"type": "adaptive"},
                                      output_config={"effort": effort})
        usage["input"] += resp.usage.input_tokens
        usage["output"] += resp.usage.output_tokens
        messages.append({"role": "assistant", "content": [block_to_dict(b) for b in resp.content]})
        if resp.stop_reason == "refusal":
            break
        uses = [b for b in resp.content if b.type == "tool_use"]
        if not uses:
            messages.append({"role": "user", "content": "Continue; finish by calling submit_report."})
            continue
        results = []
        for u in uses:
            usage["tool_calls"] += 1
            if u.name == "submit_report":
                report = u.input
                results.append({"type": "tool_result", "tool_use_id": u.id, "content": "Report received."})
            elif u.name == "run_python":
                results.append({"type": "tool_result", "tool_use_id": u.id,
                                "content": run_python(u.input.get("code", ""), work, arm)})
            else:
                try:
                    content = call(u.name, u.input, work)
                    results.append({"type": "tool_result", "tool_use_id": u.id, "content": content})
                except Exception as e:  # a failing tool is information for the agent, not a crash
                    results.append({"type": "tool_result", "tool_use_id": u.id, "is_error": True,
                                    "content": f"{type(e).__name__}: {e}"})
        messages.append({"role": "user", "content": results})
        if report is not None:
            break
    usage["seconds"] = round(time.time() - t0, 1)
    (out_dir / "transcript.json").write_text(json.dumps({"case": inp, "arm": arm, "model": MODEL, "effort": effort,
                                                         "usage": usage, "messages": messages}, indent=1,
                                                        default=str))
    if report is not None:
        (out_dir / "report.json").write_text(json.dumps(report, indent=2))
    return report is not None, usage


def main():
    ap = argparse.ArgumentParser(description="Run an agent arm (bare or tools) over test-set cases.")
    ap.add_argument("--arm", choices=["bare", "tools"], required=True, help="bare = Claude + Python only")
    ap.add_argument("--split", choices=["dev", "heldout"], default="dev", help="test-set split to run")
    ap.add_argument("--cases", nargs="*", default=None, help="case ids to run (default: all in the split)")
    ap.add_argument("--run-name", required=True, help="output folder under eval/runs/")
    ap.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"],
                    help="output_config.effort for every call (same for both arms)")
    ap.add_argument("--max-turns", type=int, default=25, help="model calls per case before giving up")
    ap.add_argument("--test-set", default=str(ROOT / "data" / "test_set"), help="test-set root")
    args = ap.parse_args()

    sys.path.insert(0, str(ROOT / "src"))
    from ramanlens.tracing import anthropic_client, trace_run

    client = anthropic_client()
    split_dir = Path(args.test_set) / args.split
    cases = sorted(d for d in split_dir.iterdir() if (d / "input.json").exists())
    if args.cases:
        cases = [d for d in cases if d.name in set(args.cases)]
    for d in cases:
        out = ROOT / "eval" / "runs" / args.run_name / args.arm / d.name
        with trace_run("ramanlens.eval_case", inputs={"case": d.name, "arm": args.arm}) as run:
            ok, usage = run_case(client, d, out, args.arm, args.effort, args.max_turns)
            run.outputs = {"submitted": ok, **usage}
        print(f"{args.arm} {d.name}: {'ok' if ok else 'NO REPORT'} {usage}", flush=True)


if __name__ == "__main__":
    main()
