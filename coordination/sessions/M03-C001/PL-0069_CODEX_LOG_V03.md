# PL-0069 — Codex Remediation Log V03

## Scope and authorization

- Authorized batch: `M03-BATCH-002`, READY, CODEX.
- Scope: PL-0069 only; PL-0070 remains accepted, PL-0068 remains OWNER_REQUIRED, and no M04 work was started.
- Prompt/criteria read: `PL-0069_CODEX_PROMPT_V03.md`, `PL-0069_CHATGPT_AUDIT_CRITERIA_V03.md`, and prior independent audit V02.

## Implementation

- Implementation commit: `6844ea6` (`fix(PL-0069): surface camera authorization and preview recovery`).
- `FoundationCameraService.start()` now returns explicit permission/restricted/unavailable errors.
- `PreviewAuthorizationResolver` maps authorization and service failures to visible preview states.
- `PreviewLifecyclePolicy` now provides idempotent attach/detach helpers.
- `NextLevelPreviewViewController` checks AVFoundation authorization, requests access when appropriate, reattaches after disappearance, and displays actionable denial/restriction/unavailable messages.

## Validation

- `git diff --check`: passed.
- `$env:PYTHONPATH=(Join-Path (Get-Location) 'core/src'); python -m pytest -q`: `162 passed, 4 skipped, 1 deselected, 1 warning`.
- Native Xcode/iPhone execution: unavailable on this Windows workspace; not claimed.
- Protected-file review: `TASKS.md` and ChatGPT audit artifacts were not modified.
- Privacy/signing review: no secrets, credentials, private assets, caches, or signing material added.

## Prior finding mapping

- Authorization/error visibility: fixed by `PreviewAuthorizationResolver`, explicit foundation errors, and UIKit status messages.
- Reappearance/duplicate attachment: fixed by `attachIfNeeded`, `detachIfNeeded`, and reattachment on `viewDidAppear`.
- Deterministic coverage: foundation policy behavior remains covered by the existing XCTest target; native execution is pending an Apple host.

READY_FOR_INDEPENDENT_AUDIT
