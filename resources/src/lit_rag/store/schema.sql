-- Storage projection schema (ADR-0004) — PostgreSQL + pgvector.
--
-- One instance holds the derived projections of the canonical BlockNode trees:
--   * catalog     — one row per CITABLE node (parsed root docs + resolved reference stubs);
--                   partly AUTHORED identity (the citable_key spine), not purely derived
--   * cites       — the corpus citation graph (adjacency list; recursive-CTE traversal)
--   * chunks      — the embedding units ("search small, resolve large"), with pgvector HNSW
--   * chunk_cites — chunk-level citation relation, hydrated at serve time (ADR-0007)
--
-- The projections are REGENERABLE from output/parsed/*/tree.json — drop them and re-ingest, nothing is
-- lost. The trees + the catalog identity are the source of truth (design §3 step 7). The CITABLE KEY
-- (DOI when resolved, else the content hash) is the spine joining tree <-> catalog <-> chunk <-> blob.

CREATE EXTENSION IF NOT EXISTS vector;

-- ── catalog: one row per citable entity ────────────────────────────────────────────────────────
-- A parsed paper/thesis (is_parsed = true, has a tree) and a resolved reference stub (is_parsed =
-- false, metadata only) are the SAME KIND OF THING keyed by citable_key (design §4) — both live here
-- so the importance prior can read a cited work's signals even when we never parsed its PDF.
CREATE TABLE IF NOT EXISTS catalog (
    citable_key           TEXT PRIMARY KEY,          -- DOI when resolved, else content hash
    doi                   TEXT,
    title                 TEXT,
    authors               JSONB,                     -- ordered list of author display names
    journal               TEXT,
    year                  INTEGER,                   -- derived from published_date
    published_date        TEXT,                      -- partial-precision ISO: "2021" | "2021-08" | "2021-08-14"
    kind                  TEXT NOT NULL DEFAULT 'paper',   -- paper | thesis | reference | dataset
    is_parsed             BOOLEAN NOT NULL DEFAULT FALSE,  -- true = full tree exists; false = reference stub
    pdf_path              TEXT,
    tree_path             TEXT,
    n_pages               INTEGER,
    parse_status          TEXT,
    -- Importance-prior signals (retrieval §5.2). published_date is immutable+intrinsic (also on the
    -- tree); citation_count is the CATALOG-ONLY drifting metric (CrossRef is-referenced-by-count),
    -- held with its fetch date and refreshable on its own cadence without re-parsing.
    citation_count        INTEGER,
    citation_count_as_of  TIMESTAMPTZ,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- A bare, undated count is age-confounded => INVALID. Enforce the §5 invariant in the DB itself.
    CONSTRAINT citation_count_requires_as_of
        CHECK (citation_count IS NULL OR citation_count_as_of IS NOT NULL)
);

-- ── cites: corpus citation graph (inter-document edges; ADR-0003) ───────────────────────────────
-- One edge per RESOLVED citation (citing doc -> cited work's DOI). Abstained references (no DOI)
-- produce no edge here — abstain over fabricate. A relational edge table IS the graph at this scale;
-- recursive CTEs give transitive traversal (ADR-0004), no graph DB warranted.
CREATE TABLE IF NOT EXISTS cites (
    from_key  TEXT NOT NULL REFERENCES catalog(citable_key) ON DELETE CASCADE,
    to_key    TEXT NOT NULL,                  -- DOI of the cited work (may not yet be a catalog row)
    marker    TEXT,                           -- in-text marker that anchored it, e.g. "[17]"
    PRIMARY KEY (from_key, to_key)
);
CREATE INDEX IF NOT EXISTS cites_to_key_idx ON cites (to_key);  -- "who cites X" (backward traversal)

-- ── chunks: derived embedding units ────────────────────────────────────────────────────────────
-- One row per embeddable leaf (the "search small" unit). text + page range are DENORMALIZED from the
-- tree so a hit cites "p. 4" and filters by page without re-reading tree.json. heading_path keeps the
-- section trail for "resolve large" (expand a hit to its enclosing section). embedding is SciNCL
-- (768-d); NULL until embedded, so ingest can write rows first and embed in a second pass.
CREATE TABLE IF NOT EXISTS chunks (
    id            BIGSERIAL PRIMARY KEY,
    citable_key   TEXT NOT NULL REFERENCES catalog(citable_key) ON DELETE CASCADE,
    node_path     TEXT NOT NULL,              -- the leaf's hierarchical id within the tree
    node_type     TEXT NOT NULL,
    heading_path  TEXT,                       -- "Methods > Sample growth" — the section trail
    text          TEXT NOT NULL,
    page_start    INTEGER,
    page_end      INTEGER,
    embedding     vector(768),
    parser_version TEXT,                      -- derived-data provenance: which parser code built this
    UNIQUE (citable_key, node_path)           -- re-ingest reconciles on this key (delete+reinsert)
);
-- additive migration for stores created before the provenance stamp (review F4); rows from
-- pre-stamp trees stay NULL ("unknown") until their paper is re-ingested from a re-parsed tree
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS parser_version TEXT;

-- HNSW for ANN. cosine ops: SciNCL similarity is angular. Rows with NULL embedding are simply
-- absent from the index until filled.
CREATE INDEX IF NOT EXISTS chunks_hnsw_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_citable_key_idx ON chunks (citable_key);

-- ── lexical channel: full-text search over chunk text (hybrid retrieval, design §5.2) ────────────
-- The PRECISION half of hybrid search. An embedding model collapses the discriminating tokens science
-- turns on (CrSBr vs CrCl3, Fe3GeTe2 vs Fe5GeTe2) into "nearby"; a lexical index matches them EXACTLY,
-- so almost-right stops outranking exact. A GENERATED column keeps the tsvector always in sync with
-- `text` (no app code, no drift on re-ingest) and BACKFILLS existing rows the moment this runs — so
-- hybrid retrieval works over an already-ingested corpus after a plain `store init`, with no re-embed.
-- GIN is the standard FTS index; the 'english' config gives stemming for prose (the 2-arg form is
-- IMMUTABLE, required for a generated column). Fusion of the two channels is Reciprocal Rank Fusion,
-- done in the app layer (rank_fusion.py) so the fusion logic stays offline-testable, not in SQL.
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS
    tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', coalesce(text, ''))) STORED;
CREATE INDEX IF NOT EXISTS chunks_tsv_gin_idx ON chunks USING gin (tsv);

-- ── chunk_cites: which references each embedded chunk cites (ADR-0007) ───────────────────────────
-- "Embed the science, join the provenance." The chunk text is the paper's own science; the works it
-- cites are NOT embedded — they are a chunk-level relation resolved at SERVE time (hydration toggle)
-- and appended by ID, never fuzzy-matched. This mirrors the paper-level `cites` graph at chunk
-- granularity; ref_key is the cited work's DOI (a catalog row once resolved, like cites.to_key — no
-- FK, same abstain-over-fabricate reason). Idempotent per document: ingest deletes+reinserts a doc's
-- rows (regenerable projection). The ref_key index answers "who cites X, and in which chunk".
CREATE TABLE IF NOT EXISTS chunk_cites (
    citable_key  TEXT NOT NULL,             -- the citing document
    node_path    TEXT NOT NULL,             -- the citing chunk within it (a chunks row)
    ref_key      TEXT NOT NULL,             -- DOI of the cited work
    marker       TEXT,                      -- in-text marker that anchored it, e.g. "[16]"
    PRIMARY KEY (citable_key, node_path, ref_key),
    FOREIGN KEY (citable_key, node_path)
        REFERENCES chunks (citable_key, node_path) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS chunk_cites_ref_key_idx ON chunk_cites (ref_key);
