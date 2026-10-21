"""Similarity metrics for the parsing eval — text + LaTeX, all offline.

The default math-similarity is a **normalised LaTeX-token edit distance** (cheap, no deps): good for
*tracking* whether equation fidelity is trending up. The field SOTA is **CDM (Character Detection
Matching)** — render both LaTeX strings to images and match at character level, so two strings that
render identically score as correct (edit distance wrongly penalises that). CDM is heavy (torch +
rendering) and lives in ``opendatalab/UniMERNet``; we keep it an *optional, lazily-imported* backend
(``cdm_similarity``) switched on only for the real equation-fidelity eval — never in the gate.
"""

from __future__ import annotations

import re

# --- normalisation ------------------------------------------------------------------------------

_MATH_DELIM = re.compile(r"\$+")
_CMD = re.compile(r"\\[a-zA-Z@]+\*?")  # \frac, \mathbf, \alpha, \section*
_SPACING = re.compile(r"\\[,;:!> ]")  # \, \; \! thin/med spaces
_BRACES = re.compile(r"[{}]")
# strip non-word AND underscores (LaTeX subscript '_' is a \w char but a separator for prose)
_NONWORD = re.compile(r"[\W_]+", re.UNICODE)
_WS = re.compile(r"\s+")


def normalize_text(s: str | None) -> str:
    """Aggressive normalisation for prose fields (title/section/caption): drop math, LaTeX commands,
    braces and punctuation; lowercase; collapse whitespace. Designed so a parser that strips LaTeX
    markup ('Co$_{20}$' -> 'Co20') still matches the source."""
    if not s:
        return ""
    s = _MATH_DELIM.sub(" ", s)
    s = _SPACING.sub(" ", s)
    s = _CMD.sub(" ", s)
    s = _BRACES.sub(" ", s)
    s = _NONWORD.sub(" ", s.lower())
    return _WS.sub(" ", s).strip()


def normalize_latex(s: str | None) -> str:
    """Light normalisation for equation bodies: strip whitespace, thin-spaces, \\left/\\right and
    braces — the syntactic noise that differs between equivalent renderings — without touching the
    structural commands. A coarse stand-in for CDM's render-and-compare."""
    if not s:
        return ""
    s = _SPACING.sub("", s)
    s = re.sub(r"\\left|\\right|\\,|\\!|\\;|\\:|\\quad|\\qquad", "", s)
    s = _BRACES.sub("", s)
    return _WS.sub("", s)


# --- edit distance ------------------------------------------------------------------------------


def levenshtein(a: str, b: str) -> int:
    """Classic O(len(a)*len(b)) edit distance (iterative two-row)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _ratio(a: str, b: str) -> float:
    """1 - normalised edit distance; 1.0 == identical, 0.0 == nothing shared. Empty/empty == 1.0."""
    if not a and not b:
        return 1.0
    n = max(len(a), len(b))
    return 1.0 - levenshtein(a, b) / n if n else 1.0


def text_similarity(a: str | None, b: str | None) -> float:
    return _ratio(normalize_text(a), normalize_text(b))


def latex_similarity(a: str | None, b: str | None) -> float:
    """Default math metric: normalised-LaTeX edit-distance ratio in [0, 1]."""
    return _ratio(normalize_latex(a), normalize_latex(b))


def cdm_similarity(a: str | None, b: str | None) -> float:
    """Optional CDM backend (render + character-detection match). Lazily imports the heavy
    UniMERNet/cdm stack; raises if it is not installed so the caller can fall back to
    ``latex_similarity``. Never imported by the gate."""
    try:
        from cdm import evaluate_cdm  # type: ignore  # noqa: F401
    except ImportError as e:  # pragma: no cover - exercised only in real equation-fidelity runs
        raise RuntimeError(
            "CDM backend not installed; install opendatalab/UniMERNet's cdm extra or use "
            "latex_similarity. See docs/research/parsing-eval-harness.md."
        ) from e
    raise NotImplementedError(  # pragma: no cover - wired when the real eq-fidelity eval lands
        "cdm_similarity adapter pending — see Open decisions in the design note."
    )
