# PL-0048 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CHATGPT_AUDIT_CRITERIA_V01.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CODEX_LOG_V01.md

Audited implementation commit: `b3c3d4ee70c2c92ee62b918c8077f7b1e2a6303c`

## Blocking findings

### ARKit-to-PackScan axis conversion is incomplete

The PackScan document freezes `+Z` as forward into the scene, but says the ARKit transform is converted by copying the native column-major matrix into row-major element order.

Apple documents ARKit as right-handed, but the ARKit camera-local Z axis points away from the device on the screen side; for gravity world alignment the viewing direction is along negative Z. A memory-layout transpose/copy does not by itself convert that camera-axis convention into PackScan's declared +Z-forward convention.

The contract therefore needs an explicit basis-change/sign-flip transform, with the exact formula/order frozen and tested.

### Machine contract omissions

- `coordinate_convention` is optional in the JSON Schema even for available/degraded poses.
- translation units for the homogeneous matrices are not frozen explicitly (ARKit world translation semantics are metric and the PackScan contract must state the stored unit).
- status/tracking-state combinations are not constrained, so contradictory states such as `status=available` with `tracking_state=not_available` can validate.

## Criterion disposition

1-6: PASS  
7: **FAIL** — the frozen PackScan/ARKit coordinate conversion is incomplete.  
8-9: PASS  
10: **FAIL** — documented conversion does not actually account for the ARKit/PackScan forward-axis difference.  
11: PASS  
12: **FAIL** — fixtures do not test basis conversion or contradictory status/tracking combinations.  
13: PASS  
14: **FAIL** — transform units and convention enforcement are incomplete.  
15-17: PASS  
18: **FAIL** — a material cross-language pose-coordinate ambiguity remains.

Result: **13 / 18 PASS, 5 FAIL**

## Required remediation

Freeze and document the exact ARKit-to-PackScan basis conversion, including:
- source and destination handedness/axis directions;
- camera viewing direction;
- matrix multiplication/order convention;
- translation unit;
- quaternion conversion derived from the same basis change.

Require `coordinate_convention` in stored available/degraded pose records and constrain valid status/tracking-state combinations.

Add synthetic fixtures/tests that transform known ARKit basis vectors/poses into the expected PackScan basis and reject contradictory tracking states.

Decision: **CHANGES_REQUIRED**
