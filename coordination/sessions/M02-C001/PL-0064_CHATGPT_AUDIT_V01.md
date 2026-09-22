# PL-0064 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0064_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0064_CHATGPT_AUDIT_CRITERIA_V01.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0064_CODEX_LOG_V01.md

Audited implementation commit: 10a7f1d6220e0ae337ef5af316037d2847b3b076

## Independent result

The confidence score is deterministic, unit-labelled, fail-closed for rejected/malformed scale evidence, and explicitly provisional rather than a physical-accuracy claim. Accepted/warning/rejected score boundaries at 0.80 and 0.60 are implemented and tested.

## Blocking findings

### Not every frozen threshold has immediate boundary coverage

The implementation freezes additional thresholds/constants:
- max relative residual = 0.05;
- max relative edge spread = 0.03;
- full marker-count credit = 4.

The committed tests do not exercise immediately-below / exact / immediately-above cases for those thresholds. Criterion 11 explicitly requires boundary tests immediately around **every threshold**.

### Threshold semantics are ambiguous above the named maxima

`MAX_RELATIVE_RESIDUAL` and `MAX_RELATIVE_EDGE_SPREAD` are described as consistency-gate maxima, but `score_calibration_confidence` merely clamps their factor to zero. With four markers and otherwise perfect evidence, a residual above 0.05 can still produce score 0.60 and status `warning` / usable-for-capture. Likewise edge spread above 0.03 can still produce a usable warning score.

Either these are hard rejection maxima and must fail closed when exceeded, or they are score-normalization reference values and should be named/documented accordingly. The current naming/documentation leaves the frozen policy ambiguous.

## Criterion disposition

1-7: PASS
8: **FAIL** — residual/spread threshold semantics are not unambiguously frozen as hard gates versus scoring reference points.
9-10: PASS
11: **FAIL** — boundary tests do not surround every frozen threshold.
12: **FAIL** — current tests can miss factor-threshold drift and above-threshold usability behavior.
13-17: PASS
18: **FAIL** — a material confidence-policy/test ambiguity remains.

Result: **14 / 18 PASS, 4 FAIL**

## Required remediation

Choose and document one semantics for residual/spread thresholds:
- if they are true maximum consistency gates, reject/fail closed above them; or
- if they are only factor-normalization reference values, rename them accordingly and document that scores may remain usable above them.

Then add immediate below/exact/above boundary tests for residual 0.05, edge spread 0.03, marker-count full-credit 4, accepted score 0.80 and warning score 0.60. Add adversarial combinations where one metric is beyond its frozen boundary while other factors are strong.

Preserve the provisional/non-physical-accuracy evidence boundary.

Decision: **CHANGES_REQUIRED**
