# PL-0073 — Codex Remediation Work Order V06

Task: **PL-0073 — Focus physical-adapter evidence closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V05.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CHATGPT_AUDIT_V05.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CODEX_PROMPT_V06.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CHATGPT_AUDIT_CRITERIA_V06.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CODEX_LOG_V06.md

## Authorization

TASKS.md must authorize `M03-BATCH-006` / `READY` / `CODEX`. PL-0068 must remain unchecked / OWNER_REQUIRED. All 22 already accepted M03 children must remain accepted and unregressed.

Never edit TASKS.md or ChatGPT audit artifacts. Never start M04.

## Mission

Close the final independent-audit gap for PL-0073 without replacing the working camera architecture.

## Mandatory remediation

1. Introduce the minimum production-used injectable camera-device-control driver/protocol beneath AVFoundationFocusAdapter/CameraDeviceConfigurationCoordinator so the same production path can be exercised without a physical iPhone.
2. Preserve the current selected main-wide CameraDeviceConfigurationCoordinator and runtime CameraControlRuntimeBridge composition.
3. Add behavior tests for non-selected-device rejection, configure→adjusting focus, observed stable focus, lock-before-stable failure, lock-after-stable success, serialized configuration use, and CaptureRuntimeViewModel focus-state propagation.
4. The injected fake must exercise the same adapter logic used by the AVFoundation device wrapper; do not create a test-only parallel policy that bypasses the production adapter.

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
