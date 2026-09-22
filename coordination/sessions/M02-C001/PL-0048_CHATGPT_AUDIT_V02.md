# PL-0048 — ChatGPT Strict Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CHATGPT_AUDIT_CRITERIA_V02.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CODEX_LOG_V02.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CHATGPT_AUDIT_V01.md

Audited implementation commit: `cc7a5e15b9a80924fff42a70e8f60368c0b4d30f`
Audited log commit: `f317c9a571cae2fcf3f7585347b3774845ba5bb6`

## Blocking findings

### 1. Destination handedness is internally inconsistent

The documentation/schema names the destination convention:

`packscan_right_handed_x_right_y_up_z_forward`

and defines PackScan as X right, Y up, +Z forward into the scene.

The remediation then uses the reflection:

`B = diag(1,1,-1,1)`

to map ARKit's camera-forward -Z to PackScan +Z.

A single-axis reflection changes handedness. Apple's ARKit/Metal documentation explicitly describes flipping the Z axis as conversion from right-handed to left-handed coordinates. Apple's ARCamera documentation also states ARKit world coordinates are right-handed and the camera-space +Z axis points out of the screen side, so the viewing direction is -Z.

Authoritative references:
- https://developer.apple.com/documentation/arkit/arcamera/transform
- https://developer.apple.com/documentation/arkit/displaying-an-ar-experience-with-metal

Therefore the contract cannot simultaneously keep X right, Y up, +Z forward and truthfully label that basis right-handed. The basis conversion may be a deliberate reflection, but the destination handedness/name must match the mathematics.

The quaternion rule is consequently underspecified as a "right-handed PackScan" quaternion conversion because the destination basis label itself is wrong.

### 2. Unavailable tracking-state rule is not enforced

The Codex log says unavailable poses require `tracking_state = not_available`.

The schema's unavailable branch constrains only:
- confidence = null;
- no matrices/quaternion.

It does **not** constrain `tracking_state`.

Thus `status = unavailable`, `tracking_state = normal`, `confidence = null` remains schema-valid. No negative fixture targets this case.

## Criterion disposition

1-7: PASS  
8: **FAIL** — destination axis/handedness convention is mathematically inconsistent.  
9-11: PASS  
12: **FAIL** — unavailable/not_available pairing is not machine-enforced.  
13: **FAIL** — quaternion conversion is declared against an incorrectly labelled destination handedness.  
14: **FAIL** — tests omit the unavailable/normal contradiction and do not detect the handedness-label defect.  
15-16: PASS  
17: **FAIL** — focused evidence would not fail for the remaining two defects.  
18-21: PASS  
22: **FAIL** — material pose-contract defects remain.

Result: **16 / 22 PASS, 6 FAIL**

## Required remediation

Choose and freeze one mathematically coherent PackScan convention.

Either:
1. keep X right, Y up, +Z forward and explicitly name/define it as left-handed; update matrix/quaternion semantics accordingly, or
2. keep a right-handed destination and change another axis/convention so the basis remains right-handed.

Do not use a reflection while simultaneously claiming both source and destination bases are right-handed with only Z reversed.

Then:
- update the `coordinate_convention` identifier and documentation;
- make the quaternion rule explicitly consistent with the chosen destination basis;
- constrain `status=unavailable` to `tracking_state=not_available`;
- add a negative unavailable/normal fixture;
- add a handedness sensitivity test using basis determinant/cross-product or equivalent relationship proof.

Decision: **CHANGES_REQUIRED**
