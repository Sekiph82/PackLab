# PL-0046 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0046_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0046_CHATGPT_AUDIT_CRITERIA_V01.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0046_CODEX_LOG_V01.md

Audited implementation commit: `27e228b404859968edb58b1bb60cb78dbc2d781b`

## Independent result

The schema correctly establishes stable photo/image binding, sequence, stored pixel dimensions, explicit unavailable/not-recorded states and a closed per-photo object shape.

## Blocking findings

The frozen task required units and numeric ranges to be explicit. The implementation uses one generic `measurement` definition for focal length, exposure, ISO and white balance:

- `unit` accepts any non-empty string rather than the field-specific unit.
- `value` has no field-specific minimum/range.
- ISO is documented as an integer exposure index but the schema accepts any JSON number.
- negative focal length, exposure, ISO and Kelvin values are not rejected by the schema.
- the nonstandard keyword `"finite": true` is not a Draft 2020-12 JSON Schema validation keyword and therefore cannot serve as portable enforcement.

The current positive/negative fixtures do not exercise wrong-unit or invalid-range cases, so these defects are not sensitivity-tested.

## Criterion disposition

1-7: PASS  
8: **FAIL** — units and numeric ranges are not enforced by the schema.  
9-11: PASS  
12: **FAIL** — negative fixtures do not detect wrong units/ranges.  
13: PASS  
14: **FAIL** — dimensional metadata units/ranges are not explicit in machine truth.  
15-17: PASS  
18: **FAIL** — a material cross-language metadata contract defect remains.

Result: **14 / 18 PASS, 4 FAIL**

## Required remediation

Use field-specific schemas or constraints so:
- focal length requires `unit = "mm"` and a positive finite value;
- exposure requires `unit = "s"` and a positive finite value;
- ISO requires its frozen unit token and an integer/valid positive range;
- white balance requires a Kelvin unit token and a physically valid positive range.

Remove reliance on nonstandard `finite` validation, or encode portability-safe numeric constraints. Add negative fixtures for wrong units, negative/zero values where invalid, and fractional ISO.

Decision: **CHANGES_REQUIRED**
