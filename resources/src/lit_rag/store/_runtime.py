"""Shared runtime plumbing for the serving adapters (ADR-0009, ADR-0018).

Both transports — the MCP stdio adapter (:mod:`mcp_server`) and the OpenAPI tool server
(:mod:`http_server`) — need the same two things: a database connection and a lazily-loaded
embedder. Keeping them here means the two adapters stay *transport only*, which is the whole
point of the core/adapter seam: if either file grows retrieval logic, the seam has been lost.

Two deliberate choices, both about a long-lived multi-client server rather than a one-shot CLI:

**A connection per request, not one shared connection.** The HTTP server answers concurrent
requests from a threadpool, and a psycopg connection is not safe to share across threads. It is
also *stateful*: one failed statement leaves the connection in an aborted transaction, so a single
long-lived connection turns one bad request into every subsequent request failing. Connecting is a
few milliseconds against a container on the same host, which is far cheaper than that failure mode.

**The serving path never applies schema.** ``store init`` is an operator action. A read-only
serving surface that mutates schema on startup is a surprise waiting to happen, and ADR-0009 keeps
the serving DB read-only from the agent's side.
"""

from __future__ import annotations

import os
import threading

from . import db

_embedder = None
_embedder_lock = threading.Lock()


def connect():
    """Open a fresh connection. Caller closes it — use as a context manager."""
    return db.connect()


def get_embedder():
    """The process-wide SciNCL embedder, constructed on first use.

    Loading pulls torch + the model weights, so it is deferred until a semantic or hybrid query
    actually needs one (a purely lexical deployment never pays for it). The lock guards the
    *construction*; inference on the loaded model is left to run concurrently.
    """
    global _embedder
    if _embedder is None:
        with _embedder_lock:
            if _embedder is None:  # re-check: another thread may have won the race
                from .embed import SciNCLEmbedder

                _embedder = SciNCLEmbedder(device=os.environ.get("LITRAG_DEVICE", "cpu"))
    return _embedder
