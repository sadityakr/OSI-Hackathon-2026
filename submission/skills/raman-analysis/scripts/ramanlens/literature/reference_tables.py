"""Curated literature Raman mode tables for 2D materials, each number traceable to the paper it was read from.

The Computational Raman Database lacks graphene, 2H-MoS2 and CrSBr, and its DFT frequencies run a few percent
low, so the matcher (ramanlens.perception.library) and the agent's lookup tool prefer these measured tables. Every
mode carries its source (DOI or arXiv id) and a locator (the table, figure or page where the number was read);
modes that could not be verified are left out and listed under `omitted`.

Input: JSON files in the skill's `resources/reference_tables/`, one per material. Each has name, formula, aliases, the
conditions of the canonical measurement (laser_nm, layers, substrate, temperature_K), `modes` (the canonical set,
used for identification), `layer_dependence` (the same modes at other layer numbers or lasers),
`conditional_modes` (modes seen only under special conditions: defects, resonance, tilted samples), notes and
omitted items.
Process: files are parsed once into dataclasses and validated (positive position, label, DOI or arXiv id, locator
on every mode); per-mode conditions inherit the table conditions and override them where given. Names are
resolved case-insensitively against the table name, formula and aliases.
Output: `get_table(name)` -> ReferenceTable, `all_tables()` -> every table, `table_names()` -> canonical names.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from ramanlens import RESOURCES

TABLE_DIR = RESOURCES / "reference_tables"


# @dataclass generates the constructor and repr: these are plain records that the agent tools serialize to JSON.
@dataclass
class Source:
    citation: str
    locator: str
    doi: str | None = None
    arxiv: str | None = None


@dataclass
class Mode:
    position_cm1: float
    label: str
    irrep: str
    source: Source
    conditions: dict = field(default_factory=dict)  # table conditions merged with mode-specific overrides
    note: str = ""
    rel_intensity: float | None = None  # None: not read from a source; the matcher then weights the mode as 1


@dataclass
class ReferenceTable:
    name: str
    formula: str
    aliases: list[str]
    conditions: dict
    modes: list[Mode]
    layer_dependence: list[Mode] = field(default_factory=list)
    conditional_modes: list[Mode] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    omitted: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Plain-dict form for JSON tool output."""
        from dataclasses import asdict
        return asdict(self)


def _mode(d: dict, table_conditions: dict, where: str) -> Mode:
    s = d.get("source") or {}
    src = Source(citation=str(s.get("citation", "")), locator=str(s.get("locator", "")),
                 doi=s.get("doi") or None, arxiv=s.get("arxiv") or None)
    m = Mode(position_cm1=float(d["position_cm1"]), label=str(d["label"]), irrep=str(d.get("irrep") or ""),
             source=src, conditions={**table_conditions, **(d.get("conditions") or {})},
             note=str(d.get("note", "")), rel_intensity=d.get("rel_intensity"))
    if not (m.position_cm1 > 0 and m.label):
        raise ValueError(f"{where}: mode needs a positive position and a label: {d}")
    if not (src.doi or src.arxiv) or not src.locator:
        raise ValueError(f"{where}: mode {m.label} at {m.position_cm1} needs a DOI or arXiv id and a locator")
    return m


def _load(path: Path) -> ReferenceTable:
    d = json.loads(path.read_text(encoding="utf-8"))
    cond = dict(d.get("conditions") or {})
    where = path.name
    return ReferenceTable(
        name=d["name"], formula=d["formula"], aliases=list(d.get("aliases") or []), conditions=cond,
        modes=[_mode(m, cond, where) for m in d.get("modes") or []],
        layer_dependence=[_mode(m, cond, where) for m in d.get("layer_dependence") or []],
        conditional_modes=[_mode(m, cond, where) for m in d.get("conditional_modes") or []],
        notes=list(d.get("notes") or []), omitted=list(d.get("omitted") or []))


# lru_cache memoizes the result: the JSON files are read once per process, not on every lookup.
@lru_cache(maxsize=1)
def _tables() -> tuple[ReferenceTable, ...]:
    return tuple(_load(p) for p in sorted(TABLE_DIR.glob("*.json")))


def all_tables() -> list[ReferenceTable]:
    """Every curated table (canonical modes in `.modes`)."""
    return list(_tables())


def table_names() -> list[str]:
    return [t.name for t in _tables()]


def _key(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def get_table(name: str) -> ReferenceTable:
    """Table by name, formula or alias, case- and punctuation-insensitive ('2H-MoS2', 'MoS2', 'mos2', 'h-BN')."""
    k = _key(name)
    for t in _tables():
        if k in {_key(t.name), _key(t.formula), *(_key(a) for a in t.aliases)}:
            return t
    raise KeyError(f"no literature table for {name!r}; available: {', '.join(table_names())}")
