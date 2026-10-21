"""Addressing and safely resolving the corpus's on-disk artifacts — figures today, PDFs later.

Figures are the reason this exists (ADR-0021), but nothing here is figure-specific: it maps a URL
path onto a file inside a parsed document's directory, whatever that file is. A later "open the
whole PDF" link is a new suffix in :data:`ALLOWED_SUFFIXES`, not a second mechanism.

**Why a URL at all, when ``get_figures`` already returns a filesystem path.** A tool result is read
by the *backend*; an image in a rendered answer is fetched by the member's *browser*. Those are
different processes on different networks, and a path like ``/app/output/parsed/…`` means nothing to
a browser. The same distinction — which process makes the outbound call — is the one that has bitten
this project at every integration boundary, so it is stated here rather than rediscovered.

**Addressing is stateless and content-derived.** A URL is ``/f/<doc_id>/<relpath>``, where ``doc_id``
is the parsed directory's content hash and ``relpath`` is the file's path inside it. No registry, no
minted-id table, nothing to fall out of sync with the corpus, and the address of a figure is a
function of the figure. Re-parsing the same PDF yields the same URL; a document that is re-ingested
under new content gets a new one, which is correct rather than merely convenient.

**A mistyped address must 404, never resolve.** Sequential ids (``/f/1``, ``/f/2``) would make every
single-character slip land on a *different real figure*, rendering it under a confident caption with
nothing in the UI to reveal the substitution. In an experimental-physics answer that is worse than
no figure at all. A 16-hex content hash is sparse enough that a corrupted address is a visibly broken
image — a failure the reader can see. Legibility for the human comes from the *label* ("Figure 1"),
which is carried in the link text, not in the address.

Everything here is pure and filesystem-only, so the traversal guards are unit-testable without
standing up a server — the half of a security boundary that is easy to get wrong is the half worth
testing offline.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

# The parsed corpus root. Repo-relative by default because catalog paths are (``output/parsed/…``);
# the serving container mounts it read-only at the same relative location under its workdir.
PARSED_ROOT_ENV = "LITRAG_PARSED_ROOT"
_DEFAULT_PARSED_ROOT = "output/parsed"

# A parsed directory name: the 16-hex content hash. Anchored — this is the first traversal guard,
# and it rejects "..", absolute paths and every encoding trick before any filesystem call happens.
DOC_ID_RE = re.compile(r"^[0-9a-f]{16}$")

# What may be served. Deliberately a closed allowlist of *renderable* types: the parsed directory
# also holds ``tree.json``, ``text.txt`` and ``catalog_signals.json``, which are internal
# representations and not for publication. ``.pdf`` is listed for the whole-document link this
# route was shaped to carry later; it costs nothing to allow and avoids a second mechanism.
ALLOWED_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".pdf"})

# The URL prefix, matched by the ``location /f/`` block in kl-chat's nginx.
URL_PREFIX = "/f"

_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".pdf": "application/pdf",
}


def parsed_root() -> Path:
    """The corpus root, resolved. Read per call so a test can point it at a fixture directory."""
    return Path(os.environ.get(PARSED_ROOT_ENV) or _DEFAULT_PARSED_ROOT).resolve()


def artifact_url(doc_id: str, relpath: str) -> str:
    """The browser-facing URL for one artifact.

    **Relative on purpose.** KL Chat is reached as ``localhost:8443`` through a tunnel and as
    ``laufey.physik.uni-mainz.de:8443`` on the university network; an absolute URL would be correct
    for exactly one of them. A root-relative path is correct for both and stays correct if the
    instance ever moves.
    """
    return f"{URL_PREFIX}/{doc_id}/{relpath.lstrip('/')}"


def resolve_artifact(doc_id: str, relpath: str) -> Path | None:
    """Map ``doc_id`` + ``relpath`` to a real file inside the corpus, or ``None`` if anything is off.

    ``None`` covers every rejection — malformed id, traversal attempt, symlink escape, disallowed
    suffix, missing file — because the caller's response to all of them is the same 404. Saying
    *which* guard tripped would tell a prober what exists; a single opaque failure tells them
    nothing, and there is no legitimate client that needs to know the difference.
    """
    if not DOC_ID_RE.match(doc_id):
        return None

    suffix = Path(relpath).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        return None

    root = parsed_root()
    doc_dir = root / doc_id

    # Resolve *before* comparing: this is what defeats ``..`` segments and symlinks that point out
    # of the tree. Comparing the unresolved path would accept ``figures/../../../etc/passwd``.
    try:
        candidate = (doc_dir / relpath).resolve()
        doc_dir_resolved = doc_dir.resolve()
    except (OSError, RuntimeError):  # RuntimeError: symlink loop
        return None

    if not candidate.is_relative_to(doc_dir_resolved):
        return None
    if not candidate.is_file():
        return None
    return candidate


def media_type(path: Path) -> str:
    return _MIME.get(path.suffix.lower(), "application/octet-stream")


_FIG_STEM_RE = re.compile(r"^fig(?:ure)?[._-]?(\d+[a-z]?)$", re.I)


def display_label(label: str | None, relpath: str | None) -> str:
    """What the reader sees in the link text — "Figure 3", not a hash.

    Prefers the parser's own label and falls back to the image filename, which is where the ordinal
    reliably survives when a caption was detected but its label was not.
    """
    if label and label.strip():
        return label.strip()
    if relpath:
        m = _FIG_STEM_RE.match(Path(relpath).stem)
        if m:
            return f"Figure {m.group(1)}"
    return "Figure"


def _alt_text(label: str, caption: str | None, limit: int = 180) -> str:
    """Alt text for the image: the label, plus as much caption as is useful.

    Sanitised rather than trusted. Caption text comes from a parsed PDF, so it can contain brackets
    that would terminate the markdown link early and newlines that would break it entirely —
    producing a mangled link out of a *correct* caption. Escaping is cheaper than debugging that.
    """
    alt = label
    if caption:
        flat = " ".join(caption.split())
        if len(flat) > limit:
            flat = flat[: limit - 1].rstrip() + "…"
        alt = f"{label}: {flat}"
    return alt.replace("\\", "").replace("[", "(").replace("]", ")")


def figure_markdown(label: str, caption: str | None, url: str) -> str:
    """The exact string the model should emit to show this figure.

    Handed over ready-made for the same reason ``wiki-rag`` returns a ``citation`` field: a model
    asked to *assemble* a link from parts will occasionally assemble a wrong one, while a model
    asked to *copy* a string mostly copies it. It also means the address's length stops mattering
    for correctness — the sparse ``doc_id`` is then purely the safety net for the times the model
    improvises anyway.
    """
    return f"![{_alt_text(label, caption)}]({url})"
