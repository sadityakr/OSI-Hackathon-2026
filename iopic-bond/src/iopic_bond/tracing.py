"""Optional LangSmith spans for iopic-Bond tools.

A trimmed copy of RamanLens' tracing decorator, so iopic-Bond installs without RamanLens. When
``LANGSMITH_TRACING=true`` and ``LANGSMITH_API_KEY`` are set and ``langsmith`` is installed, each
decorated call becomes a span in project ``LANGSMITH_PROJECT`` (default ``iopic-bond``); otherwise the
decorator returns the function unchanged.

Input: environment variables above, read when a module using ``@traced`` is imported.
Process: wraps sync and async functions with ``langsmith.traceable``.
Output: spans named ``iopic.<tool>``, ``bond.<tool>``, ``figure.fetch``, ``figure.parse``.

The decision is made at import time, so the CLI loads ``.env`` before importing any tool module.
"""
from __future__ import annotations

import os
from typing import Callable, Optional


def tracing_enabled() -> bool:
    return (
        os.environ.get("LANGSMITH_TRACING", "").lower() in {"1", "true", "yes"}
        and bool(os.environ.get("LANGSMITH_API_KEY"))
    )


try:  # langsmith is optional
    from langsmith import traceable as _traceable

    _HAVE_LS = True
except Exception:  # pragma: no cover
    _traceable = None
    _HAVE_LS = False


def traced(name: str, run_type: str = "tool", tags: Optional[list[str]] = None) -> Callable:
    """Decorator: trace a function (sync or async) as a LangSmith span, or do nothing."""

    def deco(fn: Callable) -> Callable:
        if not (_HAVE_LS and tracing_enabled()):
            return fn
        project = os.environ.get("LANGSMITH_PROJECT", "iopic-bond")
        # traceable keeps the signature and handles coroutine functions itself
        return _traceable(name=name, run_type=run_type, tags=tags or [], project_name=project)(fn)

    return deco
