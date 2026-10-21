"""JSON schema of the report every agent arm must submit, shared by the runner and the scorer.

Both arms (bare and tooled) end their run by calling the `submit_report` tool with this schema, so the scorer
compares like with like. The schema is strict (all keys required, nullable where a value may be unknown) so a
report always parses.

Input:
    None; this module only defines constants.
Process:
    Defines PATTERNS (polarization classes, matching data/test_set/README.md) and REPORT_SCHEMA.
Output:
    REPORT_SCHEMA (dict, JSON Schema) and SUBMIT_TOOL (Anthropic tool definition) for import.
"""

PATTERNS = ["isotropic_par_only", "isotropic_both", "twofold", "fourfold", "silent", "other"]
PROVENANCE = ["measured", "inferred", "literature"]

_str_or_null = {"type": ["string", "null"]}
_num_or_null = {"type": ["number", "null"]}

REPORT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["candidates", "hint_verdict", "hint_reasoning", "peaks", "properties", "artifacts",
                 "citations", "limits"],
    "properties": {
        "candidates": {
            "type": "array",
            "description": "Ranked material candidates, best first, at most 5. Use a formula with optional "
                           "polytype prefix, e.g. '2H-WS2'.",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["material", "confidence", "evidence"],
                "properties": {"material": {"type": "string"}, "confidence": {"type": "number"},
                               "evidence": {"type": "string"}},
            },
        },
        "hint_verdict": {"type": "string", "enum": ["consistent", "inconsistent", "not_applicable"]},
        "hint_reasoning": {"type": "string"},
        "peaks": {
            "type": "array",
            "description": "Sample Raman peaks and substrate lines found in the data (not cosmic rays).",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["position_cm1", "fwhm_cm1", "assignment", "irrep", "pattern", "provenance", "source"],
                "properties": {
                    "position_cm1": {"type": "number"},
                    "fwhm_cm1": _num_or_null,
                    "assignment": {"type": "string", "description": "mode label or 'Si substrate' etc."},
                    "irrep": _str_or_null,
                    "pattern": {"type": ["string", "null"], "enum": PATTERNS + [None]},
                    "provenance": {"type": "string", "enum": PROVENANCE},
                    "source": {**_str_or_null, "description": "where the assignment comes from"},
                },
            },
        },
        "properties": {
            "type": "array",
            "description": "Material properties inferred from the spectrum (layer number, strain, doping, ...).",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["name", "value", "provenance", "source"],
                "properties": {"name": {"type": "string"}, "value": {"type": "string"},
                               "provenance": {"type": "string", "enum": PROVENANCE}, "source": _str_or_null},
            },
        },
        "artifacts": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False, "required": ["type", "position_cm1"],
                "properties": {"type": {"type": "string"}, "position_cm1": _num_or_null},
            },
        },
        "citations": {"type": "array", "items": {"type": "string"}},
        "limits": {"type": "array", "items": {"type": "string"},
                   "description": "what the data cannot tell, rejected hypotheses, out-of-range relations"},
    },
}

SUBMIT_TOOL = {
    "name": "submit_report",
    "description": "Submit the final analysis. Call exactly once, when the analysis is complete. The run ends here.",
    "strict": True,
    "input_schema": REPORT_SCHEMA,
}
