"""Registry of the physics relations the agent may apply, queryable by material and by input quantity.

The agent discovers what it can compute from a peak table by asking the registry which relations take a given
quantity (e.g. `delta_E2g_A1g_cm1`) or belong to a given material. Only relations whose self-tests pass should be
used; `run_self_tests` checks all of them against the numbers printed in their source papers.

Input: material names (matched case-insensitively against the relation's material and aliases) and input names.
Process: one instance per relation class, created once; filtering by material and by required or optional input.
Output: `all_relations()`, `get(name)`, `find(material=..., input_quantity=...)`, `run_self_tests()` -> list of
(relation name, message) for every failing self-test (empty when all pass).
"""

from __future__ import annotations

from functools import lru_cache

from .base import Relation
from .crsbr import CrSBrAgModeAssignment
from .graphene import GrapheneDefectDistance, GrapheneLayersFrom2DShape, GrapheneStrainDoping
from .tmd import MoS2LayerNumberFromSeparation, WS2LayerNumberFromSeparation

RELATION_CLASSES = (MoS2LayerNumberFromSeparation, WS2LayerNumberFromSeparation, GrapheneDefectDistance,
                    GrapheneStrainDoping, GrapheneLayersFrom2DShape, CrSBrAgModeAssignment)


# lru_cache makes this run once: every caller shares the same relation instances.
@lru_cache(maxsize=1)
def _instances() -> tuple[Relation, ...]:
    return tuple(cls() for cls in RELATION_CLASSES)


def all_relations() -> list[Relation]:
    return list(_instances())


def get(name: str) -> Relation:
    for r in _instances():
        if r.name == name:
            return r
    raise KeyError(f"no relation named {name!r}; known: {[r.name for r in _instances()]}")


def _matches_material(r: Relation, material: str) -> bool:
    m = material.strip().lower()
    return m in {r.material.lower(), *(a.lower() for a in r.aliases)}


def find(material: str | None = None, input_quantity: str | None = None) -> list[Relation]:
    """Relations for `material` (if given) that accept `input_quantity` as a required or optional input (if given)."""
    out = []
    for r in _instances():
        if material is not None and not _matches_material(r, material):
            continue
        if input_quantity is not None and input_quantity not in r.inputs and input_quantity not in r.optional_inputs:
            continue
        out.append(r)
    return out


def run_self_tests() -> list[tuple[str, str]]:
    failures = []
    for r in _instances():
        try:
            problems = r.run_self_tests()
        except Exception as exc:  # a crashing relation is a failing relation, not a crashing registry
            problems = [f"raised {type(exc).__name__}: {exc}"]
        failures.extend((r.name, p) for p in problems)
    return failures
