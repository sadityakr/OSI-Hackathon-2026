# Interpretation cases: the material is known, the question is what the spectra say

Identification cases (README.md) test whether an agent can name the material. Interpretation cases test what a
senior Raman researcher actually adds: reading changes across a set of spectra (thickness, defects or treatment,
temperature, strain, laser power or wavelength), judging crystal quality, spotting measurement artifacts and
caveats, and asking the right questions about the measurement. They are scored by a rubric, graded by a blind LLM
judge (`eval/judge.py`).

## Layout

```
<split>/int-<material>-<topic>-<nn>/      split: dev_interpret/ or heldout/
  input.json
  spectrum_<label>.csv  (one or more; columns shift_cm1,intensity; x ascending)
  rubric.json           the answer key (held-out rubrics: never read while building tools)
```

### input.json
```json
{
  "case_id": "int-MoS2-thickness-01",
  "kind": "interpret",
  "task": "interpret",
  "material": "2H-MoS2",
  "spectra": [
    {"file": "spectrum_A.csv", "label": "flake A", "conditions": {"laser_nm": 532, "temperature_K": 295}},
    {"file": "spectrum_B.csv", "label": "flake B", "conditions": {"laser_nm": 532, "temperature_K": 295}}
  ],
  "context": "Mechanically exfoliated flakes on 285 nm SiO2/Si. (Only what a researcher would tell a colleague; leave out what the paper concludes; some conditions may be missing on purpose.)",
  "question": "How do these spectra differ and what does that tell you about the flakes? Anything I should be careful about?"
}
```
Labels must not leak the answer (use "flake A", "spot 2", "sample 3", never "1L" or "irradiated" when that is
what the agent should infer; use a real label when the researcher would know it, e.g. a temperature or dose).

### rubric.json
```json
{
  "case_id": "int-MoS2-thickness-01",
  "source": {"paper": "author year journal DOI/arXiv", "dataset": "DOI/URL or 'synthetic'", "locator": "Fig. 2"},
  "items": [
    {"id": "f1", "kind": "finding", "weight": 2, "text": "A1g stiffens and E2g softens from A to B, so B is thicker", "locator": "Fig. 2b"},
    {"id": "c1", "kind": "caveat", "weight": 1, "text": "Absolute intensity is not a reliable layer measure on SiO2/Si (interference)", "locator": "..."},
    {"id": "q1", "kind": "question", "weight": 1, "text": "Asks for or checks the laser wavelength / calibration because ...", "locator": "..."},
    {"id": "n1", "kind": "quantitative", "weight": 2, "text": "Estimates A as monolayer (Delta about 19 cm-1)", "locator": "..."}
  ],
  "wrong_claims": [
    {"id": "w1", "penalty": 1, "text": "Claims layer number from absolute intensity alone"}
  ],
  "notes": "how the rubric was derived; what the paper does not state"
}
```
Kinds: `finding` (what changes and what it means), `quantitative` (a number with the right relation and range),
`caveat` (artifact, pitfall, limit of the inference), `question` (what to ask or check about the measurement).
Every item is something the source paper states or a textbook-level caveat with a cited source; the rubric author
never adds conclusions the paper does not support. Typical size: 4 to 10 items, 1 to 3 wrong claims.

## Report (agent output) for interpretation cases
Schema `INTERPRET_SCHEMA` in `eval/report_schema.py`: summary, observations (finding, evidence, provenance
measured/inferred/literature, source), properties, caveats, questions_for_user, citations, limits.

## Scoring
`eval/judge.py` gives the judge the input, the report and the rubric (not the arm). Per item: met 1, partly 0.5,
not 0; per wrong claim: made or not. Case score = (sum of weight x met - sum of penalties) / sum of weights,
floored at 0. Also reported: citation specificity (does each literature claim name a paper and figure/table).
