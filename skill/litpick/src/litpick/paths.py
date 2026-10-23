"""Where the library lives.

Order: the LITPICK_HOME environment variable, else the per-user data folder of the operating
system (platformdirs):

    macOS    ~/Library/Application Support/litpick
    Windows  %LOCALAPPDATA%\\litpick
    Linux    ~/.local/share/litpick  (or $XDG_DATA_HOME/litpick)

No path is ever written into the plugin, so the same files work on every machine.
"""
from __future__ import annotations

import os
from pathlib import Path

from platformdirs import user_data_dir


def library_home() -> Path:
    env = os.environ.get("LITPICK_HOME")
    home = Path(env).expanduser() if env else Path(user_data_dir("litpick", appauthor=False))
    home.mkdir(parents=True, exist_ok=True)
    return home.resolve()


def papers_dir() -> Path:
    d = library_home() / "papers"
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    return library_home() / "litpick.db"


def safe_name(key: str) -> str:
    """A folder name that is valid on Windows, macOS and Linux (no / \\ : * ? " < > |)."""
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in key)
