# PL-0066 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CHATGPT_AUDIT_CRITERIA_V01.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CODEX_LOG_V01.md

Audited implementation commit: 7bf84c76dafa89f1f7e04fd64a80bf627d146429

## Independent result

The profile model keys reuse on device/lens/camera/resolution/orientation/zoom/focus/app/model/policy versions and provides deterministic exact/same-aspect resolution handling. Key mismatch tests are substantial.

## Blocking findings

### Provenance/owner evidence is not part of the runtime reuse gate

`CalibrationProfile` stores a provenance dictionary, but `_profile_structural_errors()` never validates it. A profile whose provenance says native capture and physical measurement evidence are unavailable can still be returned as `compatible` and reusable when its key and quality fields otherwise match.

This conflicts with the documented boundary that candidate/measured calibration profiles require owner-device capture and owner physical measurement evidence, and violates the fail-closed reuse rule when compatibility/trust cannot actually be established.

### Runtime structural validation is weaker than the persisted schema

The compatibility function does not validate the stored profile against `calibration-profile.schema.json`. Examples:
- timestamps are checked only with `.endswith("Z")`, so malformed values such as `garbageZ` can pass;
- exact-match resolutions are not checked for positive dimensions;
- required/non-empty key strings and provenance enums are not enforced by the runtime gate.

Thus persisted-schema truth and reuse-runtime truth can drift.

### Coverage does not prove every logged invalidation dimension

The tests cover key dimensions, schema version, units and rejected quality, but do not cover malformed timestamps, confidence-score range, reprojection RMSE, accepted-view count, unknown resolution policy, provenance/evidence state, or invalid key dimensions even though the log claims deterministic invalidation for these states.

## Criterion disposition

1-7: PASS
8: **FAIL** — deterministic compatibility does not include all persisted structural/provenance dimensions needed for safe reuse.
9: PASS — the model stores units, provenance, timestamps and quality evidence.
10: **FAIL** — profiles can be silently reused when owner/provenance trust or schema validity is not established.
11: **FAIL** — tests do not cover every invalidation dimension claimed by the implementation/log.
12: **FAIL** — current evidence would not detect unavailable provenance or malformed-schema profiles being reused.
13-17: PASS
18: **FAIL** — runtime/schema/docs/log are not fully consistent.

Result: **13 / 18 PASS, 5 FAIL**

## Required remediation

Make profile reuse fail closed against the full persisted contract. Prefer validating the profile through the canonical calibration-profile schema or an equivalent single generated validator before compatibility logic.

At minimum enforce:
- owner/native/physical provenance required for reusable measured profiles;
- real UTC date-time parsing, not suffix-only checks;
- positive dimensions and valid/non-empty key fields;
- confidence/RMSE/view-count ranges;
- known resolution policy and schema version.

Add tests for every structural/invalidation dimension named by the contract and log, including unavailable provenance, malformed timestamp, invalid dimensions, bad score/RMSE/view count and unknown policy.

Decision: **CHANGES_REQUIRED**
