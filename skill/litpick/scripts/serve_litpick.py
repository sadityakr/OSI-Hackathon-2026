"""Start the litpick MCP server: iopic-Bond with only the parse and figure tools.

The repo is found from RAMANLENS_REPO, then .claude-plugin/repo_root.txt (written into an installed
package), then the folders above this file. The library defaults to data/raw/iopic-bond in that repo.
Paper search is not served here; it belongs to a separate literature search tool.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]


def _repo() -> Path:
    env = os.environ.get("RAMANLENS_REPO")
    if env:
        return Path(env).expanduser().resolve()
    marker = PLUGIN / ".claude-plugin" / "repo_root.txt"
    if marker.is_file():
        recorded = Path(marker.read_text(encoding="utf-8").strip()).expanduser()
        if (recorded / "iopic-bond" / "src").is_dir():
            return recorded.resolve()
    for candidate in PLUGIN.parents:
        if (candidate / "iopic-bond" / "src").is_dir() and (candidate / ".venv").is_dir():
            return candidate
    sys.stderr.write("litpick: repo not found. Set RAMANLENS_REPO.\n")
    sys.exit(1)


def main() -> None:
    root = _repo()
    os.environ.setdefault("IOPIC_BOND_HOME", str(root / "data" / "raw" / "iopic-bond"))
    os.environ["IOPIC_BOND_SEARCH"] = "off"
    for exe in (root / ".venv" / "bin" / "iopic-bond", root / ".venv" / "Scripts" / "iopic-bond.exe"):
        if exe.exists():
            os.execv(str(exe), [str(exe), "serve"])
    sys.stderr.write(f"litpick: iopic-bond is not installed in {root / '.venv'}\n")
    sys.exit(1)


if __name__ == "__main__":
    main()
