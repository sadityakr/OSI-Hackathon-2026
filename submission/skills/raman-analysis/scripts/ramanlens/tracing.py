"""LangSmith tracing for RamanLens.

Every tool in the pipeline is decorated with ``@traced("<span name>")``. When
``LANGSMITH_API_KEY`` and ``LANGSMITH_TRACING=true`` are set, each call becomes a
span in a LangSmith trace tree under the project named by ``LANGSMITH_PROJECT``
(default ``ramanlens``). When they are not set, or the ``langsmith`` package is
missing, the decorator is a no-op, so every tool still runs in Claude Code, in a
notebook or in tests without any tracing dependency.

Usage::

    from ramanlens.tracing import traced, trace_run, anthropic_client

    @traced("fit_peaks", run_type="tool")
    def fit_peaks(x, y, **kw): ...

    with trace_run("ramanlens.analyze", inputs={"file": path}) as run:
        report = analyze(path)
        run.outputs = {"report_id": report["id"]}
        report["trace_url"] = run.url

    client = anthropic_client()   # Anthropic() wrapped so model calls nest under tools

Span naming convention (keep stable, the evaluation notebook filters on these):

    ramanlens.analyze            root span, one per spectrum
    io.read                      file reader
    preprocess.*                 baseline, cosmic, normalize
    fit_peaks                    peak detection and fitting
    match_library                CRD matcher
    polarization.classify        angle-series pattern classification
    literature.lookup            curated literature mode table
    relation.list                relation registry query
    relation.<name>              one span per relation applied
    bond.<tool>                  each Valency MCP call
    literature.find_papers       Bond paper search through iopic-Bond
    figure.view                  one figure of a parsed paper (iopic-Bond library)
    figure.fetch / figure.extract / figure.select / figure.digitize
    llm                          every Anthropic call (via wrap_anthropic)
    report.write                 report assembly

Rules: never put raw spectra arrays in span inputs (hash them, store the path);
never put API keys in metadata; tag every span with ``material`` when known so
traces can be filtered per material in the LangSmith UI.
"""
from __future__ import annotations

import functools
import hashlib
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, Optional

PROJECT = os.environ.get("LANGSMITH_PROJECT", "ramanlens")


def tracing_enabled() -> bool:
    return (
        os.environ.get("LANGSMITH_TRACING", "").lower() in {"1", "true", "yes"}
        and bool(os.environ.get("LANGSMITH_API_KEY"))
    )


try:  # langsmith is optional
    import langsmith as _ls
    from langsmith import traceable as _traceable
    from langsmith.run_helpers import get_current_run_tree as _current_run

    _HAVE_LS = True
except Exception:  # pragma: no cover
    _ls = None
    _traceable = None
    _current_run = None
    _HAVE_LS = False


def traced(name: str, run_type: str = "tool", tags: Optional[list[str]] = None) -> Callable:
    """Decorator: trace a function as a LangSmith span, or do nothing."""

    def deco(fn: Callable) -> Callable:
        if not (_HAVE_LS and tracing_enabled()):
            return fn
        wrapped = _traceable(name=name, run_type=run_type, tags=tags or [], project_name=PROJECT)(fn)

        @functools.wraps(fn)
        def inner(*args, **kwargs):
            return wrapped(*args, **kwargs)

        return inner

    return deco


@dataclass
class RunHandle:
    """What ``trace_run`` yields: set ``outputs`` before the block ends."""

    name: str
    inputs: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    url: Optional[str] = None
    run_id: Optional[str] = None


@contextmanager
def trace_run(name: str = "ramanlens.analyze", inputs: Optional[dict] = None,
              metadata: Optional[dict] = None, tags: Optional[list[str]] = None) -> Iterator[RunHandle]:
    """Open a root span for one end-to-end analysis. Yields a handle whose ``url``
    is the LangSmith trace link (None when tracing is off) for embedding in the report."""
    handle = RunHandle(name=name, inputs=inputs or {})
    if not (_HAVE_LS and tracing_enabled()):
        yield handle
        return
    from langsmith.run_helpers import trace as _trace

    with _trace(name=name, run_type="chain", inputs=handle.inputs, metadata=metadata or {},
                tags=tags or [], project_name=PROJECT) as rt:
        try:
            handle.run_id = str(rt.id)
            try:
                handle.url = rt.get_url()
            except Exception:
                handle.url = None
            yield handle
        finally:
            rt.end(outputs=handle.outputs)


def add_metadata(**kw: Any) -> None:
    """Attach key-value metadata (e.g. material="MoS2") to the current span, if any."""
    if not (_HAVE_LS and tracing_enabled()) or _current_run is None:
        return
    rt = _current_run()
    if rt is not None:
        rt.extra = rt.extra or {}
        rt.extra.setdefault("metadata", {}).update(kw)


def anthropic_client(**kwargs: Any):
    """Return an Anthropic client; wrapped for LangSmith when tracing is on, so every
    model call appears as an ``llm`` span nested under the calling tool."""
    from anthropic import Anthropic

    client = Anthropic(**kwargs)
    if _HAVE_LS and tracing_enabled():
        try:
            from langsmith.wrappers import wrap_anthropic

            return wrap_anthropic(client)
        except Exception:
            return client
    return client


def spectrum_fingerprint(x, y) -> str:
    """Short stable hash of a spectrum for span inputs (never log the arrays themselves)."""
    import numpy as np

    h = hashlib.sha1()
    h.update(np.asarray(x, dtype=float).tobytes())
    h.update(np.asarray(y, dtype=float).tobytes())
    return h.hexdigest()[:12]
