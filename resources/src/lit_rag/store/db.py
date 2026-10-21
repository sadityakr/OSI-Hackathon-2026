"""Thin PostgreSQL + pgvector connection adapter (M5, ADR-0004).

Deliberately thin: it opens a connection, registers the pgvector type, and applies ``schema.sql``.
All projection/chunking *logic* is pure and lives in :mod:`projection` / :mod:`chunker`; this is the
only module that talks to a live server, so it is the only one excluded from the offline gate. ``psycopg``
is imported lazily so importing the package (and running ``make check``) never requires the driver.

Operated per the shared-machine rules (ADR-0004 §6): the DB runs in Docker, localhost-bound, data dir
on ``/data``, resource-capped — same operational category as GROBID. Connection settings come from the
environment (``.env``), defaulting to the localhost compose service.
"""

from __future__ import annotations

import os
from pathlib import Path

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def dsn_from_env() -> str:
    """Build a libpq DSN from ``PG*`` env vars (see ``.env.example``), defaulting to local compose."""
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    host = os.environ.get("PGHOST", "127.0.0.1")
    port = os.environ.get("PGPORT", "5433")  # non-default port so we never collide with a system PG
    db = os.environ.get("PGDATABASE", "litrag")
    user = os.environ.get("PGUSER", "litrag")
    pw = os.environ.get("PGPASSWORD", "litrag")
    return f"host={host} port={port} dbname={db} user={user} password={pw}"


def connect(dsn: str | None = None):
    """Open a psycopg connection with the pgvector adapter registered. Caller closes it.

    Ensures the ``vector`` extension exists *before* registering the client adapter: pgvector's
    ``register_vector`` looks up the server-side ``vector`` type, which does not exist on a fresh
    database until ``CREATE EXTENSION`` runs (that lives in ``schema.sql``, applied only *after* a
    connection is open). Creating it here — idempotent — makes ``connect`` work against a brand-new
    volume, not only one a prior ``apply_schema`` already touched.
    """
    import psycopg
    from pgvector.psycopg import register_vector

    conn = psycopg.connect(dsn or dsn_from_env())
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn.commit()
    register_vector(conn)
    return conn


def apply_schema(conn) -> None:
    """Create the catalog/cites/chunks tables + the vector extension if absent (idempotent)."""
    conn.execute(_SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
