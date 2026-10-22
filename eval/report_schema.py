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
            "description": "Material properties inferred from the spectrum. Use these names where they apply: "
                           "'layers' (integer, or 'bulk'), 'defect_level' (none/low/medium/high), 'L_D_nm' "
                           "(graphene inter-defect distance), 'strain_sign' (tensile/compressive/none), "
                           "'doping_type' (n/p/none), 'phase' (e.g. 2H, 1T'); other names are allowed.",
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

_obs = {
    "type": "object", "additionalProperties": False,
    "required": ["finding", "evidence", "provenance", "source"],
    "properties": {
        "finding": {"type": "string", "description": "one conclusion about the sample or the measurement"},
        "evidence": {"type": "string", "description": "the measured numbers it rests on (positions, widths, "
                                                     "ratios with uncertainties) and which spectra"},
        "provenance": {"type": "string", "enum": PROVENANCE},
        "source": {**_str_or_null, "description": "paper and figure/table for literature or relation claims"},
    },
}

# Report for interpretation cases (data/test_set/INTERPRET.md): the material is known; the agent explains what the
# spectra show, what to be careful about, and what to ask.
INTERPRET_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "observations", "properties", "caveats", "questions_for_user", "citations", "limits"],
    "properties": {
        "summary": {"type": "string", "description": "the answer to the researcher's question in a few sentences"},
        "observations": {"type": "array", "items": _obs},
        "properties": REPORT_SCHEMA["properties"]["properties"],
        "caveats": {"type": "array", "items": {"type": "string"},
                    "description": "artifacts, measurement pitfalls, alternative explanations, limits of relations"},
        "questions_for_user": {"type": "array", "items": {"type": "string"},
                               "description": "what you would ask about the measurement or sample, and why"},
        "citations": {"type": "array", "items": {"type": "string"}},
        "limits": {"type": "array", "items": {"type": "string"}},
    },
}

SUBMIT_TOOL = {
    "name": "submit_report",
    "description": "Submit the final analysis. Call exactly once, when the analysis is complete. The run ends here.",
    "strict": True,
    "input_schema": REPORT_SCHEMA,
}
