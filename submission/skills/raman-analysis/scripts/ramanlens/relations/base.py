"""Base classes for physics relations: equation, validity range, source paper and self-tests in one object.

A relation turns measured Raman quantities (peak positions, separations, intensity ratios) into material
properties (layer number, defect distance, strain). The agent never applies a relation it cannot trace: each one
carries the paper it comes from with a locator, the validity range stated there, and self-tests whose inputs and
expected outputs are numbers printed in that paper. Relations fail closed: outside the validity range `apply`
returns a result with `applicable=False` and the reason, never an extrapolated number.

Input: keyword arguments named after the relation's `inputs` (required) and `optional_inputs`; quantities carry
their unit in the name (`delta_E2g_A1g_cm1`, `laser_nm`).
Process: `apply` checks that the required inputs are present and finite, runs the subclass's `check` (validity
range), then its `compute`. `run_self_tests` applies the relation to each self-test input and compares every
expected output (numbers within the stated tolerance, everything else exactly).
Output: `RelationResult` (applicable, reason, values, relation name, source, notes) and, for the registry,
`Relation.describe()` as a plain dict for the agent's tool output.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field


# @dataclass generates the constructor and repr: Source, SelfTest and RelationResult are plain records.
@dataclass
class Source:
    citation: str
    locator: str  # figure, table, equation or page in the source where the numbers were read
    doi: str | None = None
    arxiv: str | None = None


@dataclass
class SelfTest:
    inputs: dict
    expected: dict
    tolerance: dict = field(default_factory=dict)  # absolute tolerance per numeric output; default 1e-6
    locator: str = ""  # where in the source the input and expected numbers are printed


@dataclass
class RelationResult:
    relation: str
    applicable: bool
    reason: str = ""
    values: dict = field(default_factory=dict)
    source: Source | None = None
    notes: list[str] = field(default_factory=list)

    def __getitem__(self, key):
        return self.values[key]

    def to_dict(self) -> dict:
        """Plain-dict form for JSON tool output."""
        return asdict(self)


class Relation:
    """One physics relation. Subclasses set the class attributes and implement `check` and `compute`."""

    name: str = ""
    material: str = ""
    aliases: tuple[str, ...] = ()  # other material names the registry should match, e.g. "2H-MoS2"
    inputs: dict[str, str] = {}  # required input name -> description with unit
    optional_inputs: dict[str, str] = {}
    outputs: dict[str, str] = {}
    equation: str = ""
    validity: dict = {}
    source: Source = Source(citation="", locator="")
    self_tests: list[SelfTest] = []
    out_of_range_example: dict = {}
    caveats: list[str] = []  # always attached to the result's notes

    def check(self, **inputs) -> str | None:
        """Return the reason the inputs are outside the validity range, or None when they are inside."""
        return None

    def compute(self, **inputs) -> dict:
        """Return the output values; only called after `check` passed."""
        raise NotImplementedError

    def apply(self, **inputs) -> RelationResult:
        """Validate the inputs, then compute. Never raises on bad physics input: it returns applicable=False."""
        missing = [k for k in self.inputs if inputs.get(k) is None]
        if missing:
            return self._closed(f"missing required input(s): {', '.join(missing)}")
        unknown = [k for k in inputs if k not in self.inputs and k not in self.optional_inputs]
        if unknown:
            return self._closed(f"unknown input(s): {', '.join(unknown)}; accepted: "
                                f"{', '.join([*self.inputs, *self.optional_inputs])}")
        for k, v in inputs.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool) and not math.isfinite(v):
                return self._closed(f"input {k} is not finite: {v}")
        reason = self.check(**inputs)
        if reason:
            return self._closed(reason)
        values = self.compute(**inputs)
        notes = list(self.caveats) + list(values.pop("_notes", []))
        # compute may also find the result outside the stated range (e.g. L_D below 10 nm) and close itself
        late_reason = values.pop("_not_applicable", None)
        if late_reason:
            return self._closed(late_reason, values=values)
        return RelationResult(relation=self.name, applicable=True, values=values, source=self.source, notes=notes)

    def _closed(self, reason: str, values: dict | None = None) -> RelationResult:
        return RelationResult(relation=self.name, applicable=False, reason=reason, values=values or {},
                              source=self.source, notes=list(self.caveats))

    def run_self_tests(self) -> list[str]:
        """Apply every self-test; return one message per mismatch (empty list when all pass)."""
        problems = []
        for i, t in enumerate(self.self_tests):
            out = self.apply(**t.inputs)
            if not out.applicable:
                problems.append(f"self-test {i} ({t.locator}): not applicable: {out.reason}")
                continue
            for key, want in t.expected.items():
                got = out.values.get(key)
                if isinstance(want, float) and not isinstance(got, bool) and isinstance(got, (int, float)):
                    tol = t.tolerance.get(key, 1e-6)
                    if abs(got - want) > tol:
                        problems.append(f"self-test {i} ({t.locator}): {key} = {got}, expected {want} +- {tol}")
                elif got != want:
                    problems.append(f"self-test {i} ({t.locator}): {key} = {got!r}, expected {want!r}")
        return problems

    def describe(self) -> dict:
        """Everything the agent needs to decide whether and how to use the relation, as a plain dict."""
        return {"name": self.name, "material": self.material, "aliases": list(self.aliases),
                "inputs": dict(self.inputs), "optional_inputs": dict(self.optional_inputs),
                "outputs": dict(self.outputs), "equation": self.equation, "validity": dict(self.validity),
                "source": asdict(self.source), "caveats": list(self.caveats),
                "self_tests": [asdict(t) for t in self.self_tests]}


def nearest_level(value: float, levels: dict[str, float], err: float) -> tuple[str, list[str]]:
    """Closest tabulated level to `value`, plus every level within `err` of it (the ones the data cannot exclude)."""
    best = min(levels, key=lambda k: abs(levels[k] - value))
    candidates = [k for k, v in levels.items() if abs(v - value) <= err]
    if best not in candidates:
        candidates.insert(0, best)
    return best, candidates
