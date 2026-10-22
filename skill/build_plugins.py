"""Pack the litpick and ramanlens plugins as .plugin files for upload to the Claude desktop app.

Input: the plugin folders skill/litpick and skill/ramanlens in this repo.
Process: zips each folder with .claude-plugin/plugin.json at the top. An uploaded plugin is copied out
of the repo, so litpick gets .claude-plugin/repo_root.txt and absolute paths to this checkout's venv
Python and server launcher. Leftover analysis outputs and caches are skipped.
Output: skill/dist/litpick.plugin and skill/dist/ramanlens.plugin.

Valency Bond is not packed: it is a separate hosted MCP server that each user connects on their own.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent
REPO = SKILL.parent
DIST = SKILL / "dist"
SKIP_NAMES = {".DS_Store", "__pycache__", "fit.png", "peaks.json", "series.png"}


def _python() -> Path:
    for py in (REPO / ".venv" / "bin" / "python", REPO / ".venv" / "Scripts" / "python.exe"):
        if py.is_file():
            return py
    sys.exit(f"no venv Python in {REPO / '.venv'}")


def _pack(name: str, manifest_edit=None, extra: dict[str, str] | None = None) -> Path:
    root = SKILL / name
    manifest = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    if manifest_edit:
        manifest_edit(manifest)
    out = DIST / f"{name}.plugin"
    DIST.mkdir(exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix == ".pyc" or any(p in SKIP_NAMES for p in path.parts):
                continue
            rel = path.relative_to(root).as_posix()
            if rel == ".claude-plugin/plugin.json":
                zf.writestr(rel, json.dumps(manifest, indent=2) + "\n")
            else:
                zf.write(path, rel)
        for rel, text in (extra or {}).items():
            zf.writestr(rel, text)
    return out


def main() -> None:
    launcher = SKILL / "litpick" / "scripts" / "serve_litpick.py"

    def litpick_manifest(m: dict) -> None:
        m["mcpServers"]["litpick"] = {"command": str(_python()), "args": [str(launcher)]}

    outs = [
        _pack("litpick", litpick_manifest, {".claude-plugin/repo_root.txt": f"{REPO}\n"}),
        _pack("ramanlens"),
    ]
    for out in outs:
        with zipfile.ZipFile(out) as zf:
            name = json.loads(zf.read(".claude-plugin/plugin.json"))["name"]
            print(f"{out.relative_to(REPO)}  plugin {name}  {len(zf.namelist())} files")


if __name__ == "__main__":
    main()
