"""Command-line access to the Raman analysis tools for the raman-analysis skill.

The same tools serve the Python agent runner (as Anthropic tool definitions) and this skill (as shell commands),
so both read the spectrum with identical code. Each subcommand is generated from the tool's own JSON schema, so
`python rl.py <tool> --help` always shows the current inputs and their meaning.

Input:
    A subcommand naming a tool in ramanlens.agent.toolset (load_spectrum, fit_peaks, match_library,
    classify_polarization, lookup_reference_modes, list_relations, apply_relation) and its inputs as options.
    Array inputs take several values (--positions_cm1 352.9 415.1); object inputs take a JSON string
    (--inputs '{"delta_E2g_A1g_cm1": 19.3}'). File paths are relative to the current folder.
Process:
    ramanlens.agent.toolset.call(name, inputs, workdir=current folder).
Output:
    The tool's JSON result on stdout: measured values carry their method, literature values their source paper
    and locator, relation results their validity verdict.
"""

import argparse
import json
import sys
from pathlib import Path

from ramanlens.agent import toolset

SKIP = {"find_papers", "view_figure"}  # literature figures come from the litpick MCP server in Claude Code
PY_TYPES = {"number": float, "integer": int, "string": str, "boolean": lambda s: s.lower() in ("1", "true", "yes")}


def build_parser():
    ap = argparse.ArgumentParser(description="Raman skill tools. `python rl.py <tool> --help` for a tool's inputs.")
    sub = ap.add_subparsers(dest="tool", required=True)
    for t in toolset.TOOLS:
        if t["name"] in SKIP:
            continue
        sp = sub.add_parser(t["name"], help=t["description"].split(". ")[0], description=t["description"])
        required = set(t["input_schema"].get("required", []))
        for name, spec in t["input_schema"].get("properties", {}).items():
            kw = {"help": spec.get("description", ""), "required": name in required, "dest": name}
            if spec.get("type") == "array":
                kw.update(nargs="+", type=PY_TYPES.get(spec.get("items", {}).get("type"), str))
            elif spec.get("type") == "object":
                kw.update(type=json.loads)
            else:
                kw.update(type=PY_TYPES.get(spec.get("type"), str))
            sp.add_argument(f"--{name}", **kw)
    return ap


def main():
    args = vars(build_parser().parse_args())
    name = args.pop("tool")
    inputs = {k: v for k, v in args.items() if v is not None}
    out = toolset.call(name, inputs, Path.cwd())
    sys.stdout.write(out if isinstance(out, str) else json.dumps(out, default=str))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
