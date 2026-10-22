"""Settings for iopic-Bond: where the library lives, the Bond token, the parse device.

Input: environment variables, optionally from a ``.env`` file (``IOPIC_BOND_ENV_FILE``, else the
nearest ``.env`` from the working directory upward).
Process: resolves each setting with a documented default.
Output: plain functions read by the store, the Bond client and the CLI.

    IOPIC_BOND_HOME      library root (default: the OS cache dir from platformdirs)
    VALENCY_BOND_TOKEN   Valency Direct API token from https://app.valency.io/settings
    VALENCY_BOND_URL     Bond endpoint (default https://mcp.valency.io/)
    IOPIC_BOND_DEVICE    Docling device, "cpu" or "cuda" (default cpu)
    IOPIC_BOND_EXCLUDE   withheld papers: arXiv ids, DOIs or title fragments (see exclude.py)
    IOPIC_BOND_EXCLUDE_FILE  the same, one entry per line in a file
"""
from __future__ import annotations

import os
from pathlib import Path

DEFAULT_BOND_URL = "https://mcp.valency.io/"


def load_env() -> None:
    """Load ``.env`` into the process environment without overriding variables already set."""
    from dotenv import find_dotenv, load_dotenv

    path = os.environ.get("IOPIC_BOND_ENV_FILE") or find_dotenv(usecwd=True)
    if path:
        load_dotenv(path, override=False)


def home() -> Path:
    env = os.environ.get("IOPIC_BOND_HOME")
    if env:
        root = Path(env).expanduser()
    else:
        from platformdirs import user_cache_path

        # appauthor=False: no extra vendor folder level on Windows
        root = user_cache_path("iopic-bond", appauthor=False)
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def bond_token() -> str | None:
    return os.environ.get("VALENCY_BOND_TOKEN") or None


def bond_url() -> str:
    return os.environ.get("VALENCY_BOND_URL", DEFAULT_BOND_URL)


def parse_device() -> str:
    return os.environ.get("IOPIC_BOND_DEVICE", "cpu")
