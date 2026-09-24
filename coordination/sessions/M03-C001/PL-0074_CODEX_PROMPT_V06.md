# PL-0074 — Codex Remediation Work Order V06

Task: **PL-0074 — Exposure physical-adapter evidence closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V05.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CHATGPT_AUDIT_V05.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CODEX_PROMPT_V06.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CHATGPT_AUDIT_CRITERIA_V06.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CODEX_LOG_V06.md

## Authorization

TASKS.md must authorize `M03-BATCH-006` / `READY` / `CODEX`. PL-0068 must remain unchecked / OWNER_REQUIRED. All 22 already accepted M03 children must remain accepted and unregressed.

Never edit TASKS.md or ChatGPT audit artifacts. Never start M04.

## Mission

Close the final independent-audit gap for PL-0074 without replacing the working camera architecture.

## Mandatory remediation

1. Use the same production-used injectable camera-device-control driver/seam as PL-0073 for AVFoundationExposureAdapter behavior.
2. Preserve the current selected main-wide coordinator, runtime control bridge, AcceptedPhotoMetadataFactory, and captureAndPersistAcceptedPhoto wiring.
3. Add behavior tests for wrong-device rejection, bias clamping, continuous metering, lock behavior, serialized configuration, runtime exposure-state propagation, and persisted exposure/ISO source values on an accepted photo.
4. Tests must drive the production adapter/composition path or its injected device driver, not only ExposurePolicy/bridge structs.

## Validation

- Add behavior-bearing tests against the production-used injected camera-device-control seam.
- Run focused tests and all relevant M03 regression/static/project checks available on the Windows host.
- Run `git diff --check`.
- Verify `git diff -- TASKS.md` is empty.
- Verify no ChatGPT audit file was edited by Codex.
- Review privacy/signing/secret scope.
- Native Xcode/iPhone success may be claimed only if genuinely executed.

Create one implementation commit, then publish the child log in a separate log-only commit.

Every user-facing repository link must be a full GitHub URL, never a local filesystem path.

End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
