# PL-0049 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CHATGPT_AUDIT_CRITERIA_V01.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CODEX_LOG_V01.md

Audited implementation commit: `b57b1ed99befc7ba308d480929c91513540b0feb`

## Blocking findings

### Native CoreMotion clock provenance is missing

The schema freezes CoreMotion samples directly into UTC timestamps and declares `source_clock = "utc"`.

Core Motion's native `CMLogItem.timestamp` is a monotonic time interval measured in seconds since device boot, not UTC. A cross-platform synchronization contract therefore needs to preserve the native monotonic timestamp and the mapping used to relate it to the UTC/photo clock, including the mapping reference/offset and uncertainty or resolution.

Without that mapping, two producers can generate different UTC timestamps from the same CoreMotion sample while both appearing schema-valid.

### Attitude reference frame is not frozen

The schema records an attitude quaternion and device-axis convention but does not record which `CMAttitudeReferenceFrame` produced the attitude. Core Motion attitude is reference-frame dependent, so the quaternion is not fully interpretable from the stored contract alone.

### Status/data consistency is not enforced

A sample marked `available` can validate with no attitude or rotation-rate data, while `unavailable` can validate with motion vectors present.

## Criterion disposition

1-6: PASS  
7: **FAIL** — attitude metadata lacks its CoreMotion reference-frame contract.  
8: **FAIL** — native boot-time to UTC synchronization provenance is not frozen.  
9: PASS  
10: **FAIL** — the contract overstates UTC precision without preserving the clock mapping evidence.  
11: PASS  
12: **FAIL** — fixtures do not exercise clock mapping/reference-frame or contradictory status/data combinations.  
13: PASS  
14: **FAIL** — time/reference-frame provenance is incomplete.  
15-17: PASS  
18: **FAIL** — a material cross-platform synchronization ambiguity remains.

Result: **12 / 18 PASS, 6 FAIL**

## Required remediation

Freeze a two-clock synchronization model. At minimum record:
- native CoreMotion monotonic timestamp in seconds since boot;
- the photo/capture clock domain;
- the measured mapping/anchor between monotonic and UTC clocks;
- mapping uncertainty/resolution and synchronization tolerance;
- the selected `CMAttitudeReferenceFrame`.

Do not discard the native timestamp after conversion.

Constrain state/data combinations so available samples contain the required motion payload, while unavailable samples cannot carry valid motion vectors. Add aligned/stale/missing fixtures that exercise the actual two-clock mapping and reference-frame fields.

Decision: **CHANGES_REQUIRED**
