"""Run one agent arm over test-set cases with headless Claude Code, with or without the RamanLens skill.

This is the skill counterpart of eval/run_agent.py. The deliverable is a Claude Code skill, so the comparison runs
the real `claude -p` agent: same model, effort, system prompt, tools (Bash, Read, Write, Edit, Glob, Grep) and
Python environment in both arms. The `skill` arm also loads the RamanLens plugin (skill/ramanlens) and the
literature MCP servers; the `bare` arm cannot import ramanlens. It needs no API key: it uses the Claude Code login.

Input:
    data/test_set/<split>/<case_id>/{input.json, spectrum.csv}. truth.json is never read or copied.
    The prompt and reporting rules are imported from eval/run_agent.py so both runners ask the same question.
    The report schema is eval/report_schema.py, enforced through `claude -p --json-schema`.
Process:
    Each case runs in a fresh folder outside the repo (so no project CLAUDE.md is loaded and relative paths cannot
    reach the test set). User-level settings, CLAUDE.md and skills are excluded with --setting-sources project; MCP
    servers come only from --mcp-config. In the bare arm a stub package on PYTHONPATH makes `import ramanlens` fail.
    Web tools and sub-agents are disallowed in both arms. Cases run in parallel threads.
Output:
    eval/runs/<run_name>/<arm>/<case_id>/{report.json, transcript.json, transcript.jsonl}, the layout eval/score.py
    reads. transcript.json carries usage (tokens, cost in USD as reported by Claude Code, turns, seconds).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
from report_schema import INTERPRET_SCHEMA, REPORT_SCHEMA  # noqa: E402
from run_agent import SYSTEM, case_prompt  # noqa: E402

PLUGIN_DIR = ROOT / "skill" / "ramanlens"
WORK_ROOT = Path(tempfile.gettempdir()) / "ramanlens-eval"

# The SDK runner ends with a submit_report tool; here the report is Claude Code's structured output instead.
FOLDER_RULE = ("The data is in the current folder. Do not look for other data or answer files elsewhere on this "
               "machine; scripts and notes provided by a skill you load may be used wherever they live.")
# The SDK runner's 'current folder only' wording made Haiku refuse to run skill scripts stored outside the case
# folder; the rule exists to keep agents away from the test set, which permission deny rules also enforce.
SYSTEM_CC = SYSTEM.replace(
    "Work in the current folder only: the data file is ./spectrum.csv. Do not read files outside this folder.",
    FOLDER_RULE + " The data file is ./spectrum.csv."
).replace(
    "Then call submit_report exactly once.",
    "Your final answer is the structured report. Python 3 with numpy, scipy, pandas, lmfit and matplotlib is "
    "available as `python`.")

SYSTEM_INTERPRET = """You are helping a researcher interpret Raman spectra of a layered (van der Waals) material
they know. The data is in the current folder. Do not look for other data or answer files elsewhere on this machine;
scripts and notes provided by a skill you load may be used wherever they live. Python 3 with numpy, scipy, pandas,
lmfit and matplotlib is available as `python`. Analyse the data quantitatively before concluding.

Answer like a senior Raman spectroscopist: what changes between the spectra and what it means for the sample
(thickness, crystal quality, defects, strain, doping, temperature, magnetic order, ...), backed by measured numbers.
Point out artifacts, measurement pitfalls and alternative explanations. List the questions you would ask about the
measurement or sample and why; the researcher is not available now, so state your assumptions instead of waiting.
Every literature or relation claim names its source (paper and figure or table). Say what the data cannot tell.
Your final answer is the structured report."""


def interpret_prompt(inp):
    lines = [f"Material: {inp['material']}", f"Context: {inp.get('context', '')}", "Spectra in this folder:"]
    for s in inp["spectra"]:
        lines.append(f"- {s['file']} ({s['label']}): conditions {json.dumps(s.get('conditions', {}))}; "
                     "columns shift_cm1,intensity")
    return "\n".join(lines) + f"\n\nQuestion: {inp['question']}"


BASE_TOOLS = ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
SKILL_TOOLS = ["Skill", "mcp__valency__*", "mcp__iopic-bond__*"]
NEVER_TOOLS = ["WebSearch", "WebFetch", "Agent", "Task"]


def mcp_config(arm, work):
    """MCP servers for the arm, written as a JSON file. The bare arm gets none."""
    servers = {}
    if arm == "skill":
        servers["valency"] = {"type": "http", "url": "https://mcp.valency.io/"}
        exe = ROOT / ".venv" / "Scripts" / "iopic-bond.exe"
        if exe.exists():
            servers["iopic-bond"] = {"command": str(exe), "args": ["serve"],
                                     "env": {"IOPIC_BOND_HOME": str(ROOT / "data" / "raw" / "iopic-bond")}}
    path = work.parent / f"_mcp_{work.name}.json"
    path.write_text(json.dumps({"mcpServers": servers}))
    return path


def blocker_dir():
    """A folder with stub packages that raise on import; put first on PYTHONPATH in the bare arm.

    PYTHONPATH entries are searched before site-packages, so the stub shadows the editable install of ramanlens.
    """
    d = WORK_ROOT / "_blocked"
    for pkg in ("ramanlens", "iopic_bond"):
        (d / pkg).mkdir(parents=True, exist_ok=True)
        (d / pkg / "__init__.py").write_text(f"raise ImportError('{pkg} is not available in this arm')\n")
    return d


def child_env(arm):
    env = dict(os.environ)
    env["PATH"] = str(ROOT / ".venv" / "Scripts") + os.pathsep + env.get("PATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    if arm == "bare":
        env["PYTHONPATH"] = str(blocker_dir())
    else:
        env.pop("PYTHONPATH", None)
    return env


LIMIT_HIT = []  # filled when the Claude usage limit (HTTP 429) is reached; remaining cases are then skipped


def run_case(case_dir, out_dir, arm, model, effort, timeout_min, run_name):
    if LIMIT_HIT:
        return case_dir.name, False, {"skipped": "usage limit reached earlier in this batch"}
    if (out_dir / "report.json").exists():
        return case_dir.name, True, {"resumed": "report already present"}
    inp = json.loads((case_dir / "input.json").read_text())
    work = WORK_ROOT / run_name / arm / case_dir.name
    for d in (out_dir, work):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    interpret = inp.get("kind") == "interpret"
    for f in case_dir.glob("spectrum*.csv"):
        shutil.copy(f, work / f.name)
    prompt, system, schema = ((interpret_prompt(inp), SYSTEM_INTERPRET, INTERPRET_SCHEMA) if interpret
                              else (case_prompt(inp), SYSTEM_CC, REPORT_SCHEMA))

    deny_test_set = {"permissions": {"deny": [f"Read(/{ROOT.as_posix()}/data/test_set/**)",
                                              f"Read(/{ROOT.as_posix()}/eval/**)"]}}
    cmd = ["claude", "-p", prompt,
           "--model", model, "--effort", effort,
           "--append-system-prompt", system,
           "--json-schema", json.dumps(schema),
           "--setting-sources", "project",
           "--settings", json.dumps(deny_test_set),
           "--strict-mcp-config", "--mcp-config", str(mcp_config(arm, work)),
           "--permission-mode", "dontAsk",
           "--allowedTools", *(BASE_TOOLS + (SKILL_TOOLS if arm == "skill" else [])),
           "--disallowedTools", *NEVER_TOOLS,
           "--output-format", "stream-json", "--verbose", "--no-session-persistence"]
    if arm == "skill":
        cmd += ["--plugin-dir", str(PLUGIN_DIR)]

    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=work, env=child_env(arm), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout_min * 60)
        stdout, stderr = p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = f"[timeout after {timeout_min} min]"

    events = []
    for line in stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    result = next((e for e in reversed(events) if e.get("type") == "result"), {})
    if result.get("is_error") and result.get("api_error_status") == 429:
        # Usage limit: leave no partial files so a resumed run retries this case.
        shutil.rmtree(out_dir, ignore_errors=True)
        LIMIT_HIT.append(f"{case_dir.name}: {result.get('result')}")
        return case_dir.name, False, {"rate_limited": str(result.get("result"))}
    report = result.get("structured_output")
    u = result.get("usage", {})
    usage = {"input": u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
             + u.get("cache_creation_input_tokens", 0),
             "output": u.get("output_tokens", 0), "cost_usd": result.get("total_cost_usd"),
             "turns": result.get("num_turns"), "seconds": round(time.time() - t0, 1),
             "tool_calls": sum(1 for e in events if e.get("type") == "assistant"
                               for b in e.get("message", {}).get("content", []) if b.get("type") == "tool_use")}

    (out_dir / "transcript.jsonl").write_text(stdout, encoding="utf-8")
    (out_dir / "transcript.json").write_text(json.dumps(
        {"case": inp, "arm": arm, "model": model, "effort": effort, "usage": usage, "stderr": stderr[-4000:],
         "messages": events}, indent=1, default=str), encoding="utf-8")
    if report is not None:
        (out_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return case_dir.name, report is not None, usage


def main():
    ap = argparse.ArgumentParser(description="Run a Claude Code agent arm (bare or skill) over test-set cases.")
    ap.add_argument("--arm", choices=["bare", "skill"], required=True,
                    help="bare = Claude Code + Python only; skill = plus the RamanLens plugin and literature MCP")
    ap.add_argument("--split", choices=["dev", "dev_hard", "dev_interpret", "heldout"], default="dev",
                    help="test-set split (dev_hard: harder identification cases; dev_interpret: interpretation "
                         "cases, data/test_set/INTERPRET.md)")
    ap.add_argument("--kind", choices=["all", "identify", "interpret"], default="all",
                    help="run only identification cases, only interpretation cases, or both")
    ap.add_argument("--cases", nargs="*", default=None, help="case ids to run (default: all in the split)")
    ap.add_argument("--run-name", required=True, help="output folder under eval/runs/")
    ap.add_argument("--model", default="claude-sonnet-5-5", help="same model for both arms")
    ap.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"],
                    help="reasoning effort (same for both arms)")
    ap.add_argument("--parallel", type=int, default=3, help="cases run at the same time")
    ap.add_argument("--timeout-min", type=int, default=20, help="wall-clock limit per case")
    ap.add_argument("--test-set", default=str(ROOT / "data" / "test_set"), help="test-set root")
    args = ap.parse_args()

    if args.arm == "skill" and not (PLUGIN_DIR / ".claude-plugin" / "plugin.json").exists():
        sys.exit(f"skill arm needs the plugin at {PLUGIN_DIR}")
    split_dir = Path(args.test_set) / args.split
    cases = sorted(d for d in split_dir.iterdir() if (d / "input.json").exists())
    if args.cases:
        cases = [d for d in cases if d.name in set(args.cases)]
    if args.kind != "all":
        cases = [d for d in cases if d.name.startswith("int-") == (args.kind == "interpret")]

    def one(d):
        out = ROOT / "eval" / "runs" / args.run_name / args.arm / d.name
        return run_case(d, out, args.arm, args.model, args.effort, args.timeout_min, args.run_name)

    # ThreadPoolExecutor: runs `one` on several cases at once; each thread just waits on its own claude process.
    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        for name, ok, usage in pool.map(one, cases):
            print(f"{args.arm} {name}: {'ok' if ok else 'NO REPORT'} {usage}", flush=True)
    if LIMIT_HIT:
        print(f"USAGE LIMIT reached ({LIMIT_HIT[0]}); rerun the same command after the reset to resume.")
        sys.exit(2)


if __name__ == "__main__":
    main()
