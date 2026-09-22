# PL-0063 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0063_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0063_CHATGPT_AUDIT_CRITERIA_V01.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0063_CODEX_LOG_V01.md

Audited implementation commit: f81d9741ef6a18fb8248c5fabf621ab8a0bb2251

## Blocking finding

The estimator does not fully reject degenerate marker geometry.

`_valid_observation()` checks that the four edge lengths are finite and positive, but it does not check polygon area, convexity or self-intersection. Four collinear points can have positive adjacent/closing edge lengths while enclosing zero area, and a bow-tie/self-crossing quadrilateral can likewise reach the scale calculation.

The committed degenerate test exercises only a zero-size square, which produces zero-length edges. It does not protect the actual zero-area/self-crossing boundary.

## Criterion disposition

1-8: PASS
9: **FAIL** — degenerate geometry is not comprehensively rejected.
10: PASS
11: **FAIL** — synthetic ground-truth coverage omits zero-area/self-crossing degeneracy.
12: **FAIL** — current regression would not detect those broken geometries.
13-17: PASS
18: **FAIL** — a material scale-input validation defect remains.

Result: **14 / 18 PASS, 4 FAIL**

## Required remediation

Before using an observation for scale, validate the ordered quadrilateral as non-degenerate. At minimum reject near-zero polygon area and self-intersection; preferably require a simple convex quadrilateral with a documented numerical tolerance.

Add synthetic tests for collinear four-corner input, bow-tie/self-crossing input and a valid perspective-distorted convex quadrilateral. Preserve the existing weighted scale/residual/provenance behavior.

Decision: **CHANGES_REQUIRED**
