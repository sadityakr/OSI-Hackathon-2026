"""Run the bare and the literature-in-the-loop (skill v4) arms over test-set cases with headless Claude Code.

eval/run_claude_code.py was written for skill v3: its skill arm gets the unfiltered Valency MCP server and runs in
don't-ask mode, which refuses the Bash `cp` that copies the v4 notebook template. This wrapper reuses that runner
unchanged (same prompts, schemas, isolation and scoring layout) and swaps only the parts that define the v4 arm.

Input:
    Same command line as eval/run_claude_code.py (--arm, --split, --kind, --cases, --run-name, --model, ...).
    The v4 plugin in submission/demo/plugin-v4, the iopic-bond library in data/raw/iopic-bond, the withheld-paper
    list data/test_set/withheld_papers.txt, and .env (VALENCY_BOND_TOKEN) when it exists.
Process:
    Skill arm: the v4 plugin plus iopic-bond only, with IOPIC_BOND_EXCLUDE_FILE set, so literature search goes
    through Bond but the source paper of each case is hidden and refused. No direct Valency server (its results
    cannot be filtered). Both arms run in accept-edits mode (file writes inside the case folder are allowed) and
    are denied reads of answer keys, earlier results, demo outputs and planning documents.
Output:
    eval/runs/<run_name>/<arm>/<case_id>/{report.json, transcript.json, transcript.jsonl}, scored by
    eval/judge.py (interpretation) or eval/score.py (identification).
"""
import json
import subprocess
import tempfile
from pathlib import Path

import run_claude_code as rc

ROOT = rc.ROOT
rc.PLUGIN_DIR = ROOT / "submission" / "demo" / "plugin-v4"
rc.WORK_ROOT = Path(tempfile.gettempdir()) / "litloop-eval"
rc.SKILL_TOOLS = ["Skill", "mcp__iopic-bond__*"]

# Paths an agent could use to find answers or earlier answers to the same cases.
DENY = [f"Read(/{(ROOT / p).as_posix()})" for p in (
    "data/test_set/**", "eval/**", "results/**", "docs/**", "data/raw/spectra/**", "submission/*.md",
    "submission/results.html", "submission/skills/**", "submission/demo/crsbr-thickness/**",
    "submission/demo/crsbr-defects/**", "submission/demo/dryruns/**", "submission/demo/config/**")]


def mcp_config(arm, work):
    """iopic-bond with the withheld-paper filter for the skill arm; no servers for the bare arm."""
    servers = {}
    if arm == "skill":
        env = {"IOPIC_BOND_HOME": str(ROOT / "data" / "raw" / "iopic-bond"),
               "IOPIC_BOND_EXCLUDE_FILE": str(ROOT / "data" / "test_set" / "withheld_papers.txt")}
        if (ROOT / ".env").exists():  # the server starts in the case folder, where .env is not found
            env["IOPIC_BOND_ENV_FILE"] = str(ROOT / ".env")
        servers["iopic-bond"] = {"command": str(ROOT / ".venv" / "Scripts" / "iopic-bond.exe"),
                                 "args": ["serve"], "env": env}
    path = work.parent / f"_mcp_{work.name}.json"
    path.write_text(json.dumps({"mcpServers": servers}))
    return path


rc.mcp_config = mcp_config

_run = subprocess.run


def _run_v4(cmd, *args, **kwargs):
    """Rewrite the claude command that run_case builds: accept-edits mode and the wider read-deny list."""
    if cmd and cmd[0] == "claude":
        cmd = list(cmd)
        cmd[cmd.index("--permission-mode") + 1] = "acceptEdits"
        cmd[cmd.index("--settings") + 1] = json.dumps({"permissions": {"deny": DENY}})
    return _run(cmd, *args, **kwargs)


rc.subprocess.run = _run_v4

if __name__ == "__main__":
    rc.main()
