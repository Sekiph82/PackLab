# PL-0047 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0047_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0047_CHATGPT_AUDIT_CRITERIA_V01.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0047_CODEX_LOG_V01.md

Audited implementation commit: `bb86aa2bef2a61719bcffae32f2f4c5c074566d6`

## Independent result

The contract correctly freezes the coordinate origin, row-major 3x3 convention, reference dimensions, dimension-policy names, status/provenance states and synthetic measured/unavailable examples.

## Blocking finding

The distortion contract is documented more strictly than the machine schema enforces.

The schema allows:
- `brown_conrady` or `fisheye` with an arbitrary `coefficient_order` string array;
- omitted `coefficients`;
- coefficient-order and coefficient-value arrays of different lengths;
- `model = "none"` with non-empty coefficient metadata.

The documentation names Brown-Conrady and OpenCV fisheye coefficient ordering, but a cross-language PackScan producer/consumer must not rely on prose while the schema accepts contradictory data.

## Criterion disposition

1-9: PASS  
10: **FAIL** — model-specific coefficient ordering/content is not actually enforced.  
11: PASS  
12: **FAIL** — no negative fixture proves wrong order/length/model combinations are rejected.  
13: PASS  
14: **FAIL** — distortion model/order provenance is not fully frozen in machine truth.  
15-17: PASS  
18: **FAIL** — a material cross-language intrinsics ambiguity remains.

Result: **14 / 18 PASS, 4 FAIL**

## Required remediation

Make distortion model branches explicit in JSON Schema, for example:
- `none`: empty coefficient order and empty coefficient values;
- `fisheye`: exact order `[k1,k2,k3,k4]` and exactly four coefficients;
- `brown_conrady`: one explicitly supported order/version with matching coefficient count.

If multiple Brown-Conrady variants are needed, version/name them explicitly rather than accepting arbitrary strings.

Add negative fixtures for wrong order, missing coefficients and order/value length mismatch.

Decision: **CHANGES_REQUIRED**
