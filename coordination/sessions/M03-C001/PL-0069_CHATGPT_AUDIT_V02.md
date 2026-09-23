# PL-0069 — ChatGPT Independent Audit V02

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CHATGPT_AUDIT_CRITERIA_V02.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_LOG_V02.md
Implementation commit: `86910666442722afa24147e185f771110f078596`
Child log commit: `39dd3ed`
Authorized batch start: `fd1488f69366db37e45f2697edd8c7bd9e21611d`

## Independent findings

The child has a real UIKit/SwiftUI bridge, keeps NextLevel-specific preview ownership out of ordinary SwiftUI layout code, preserves the exact NextLevel 0.19.1 project dependency, adds simulator-safe placeholder UI, and adds an independently testable lifecycle policy. Scope and protected-file handling are otherwise consistent with the frozen child boundary.

However two mandatory behaviors are materially incomplete.

### Finding 1 — authorization/error states are declared but not wired into the real preview flow

`PreviewSurfaceState` declares `loading`, `running`, `denied`, `restricted`, `simulatorUnavailable`, `unavailable`, and `error`, but the physical-device `NextLevelPreviewViewController` does not use that state model to gate or present camera authorization/session failures.

The implementation:
- attaches `nextLevel.previewLayer` in `viewDidLoad`;
- hides the status label immediately;
- calls `nextLevel.start()` from `viewDidAppear`;
- then unconditionally sets the label text to "Camera preview running".

There is no inspected branch that maps denied/restricted/unavailable/start failure into the required visible fail-closed UI. This does not satisfy criterion 11 / Requirement B.

### Finding 2 — preview attachment is not idempotently restored after disappearance

`viewDidDisappear` calls `detachPreview()`, removing the preview layer and decrementing the lifecycle attachment count. On a later `viewDidAppear`, the controller calls `nextLevel.start()` but does **not** call `attachPreviewIfPossible()` again.

Because `viewDidLoad` normally runs only once for the controller lifetime, a disappear → reappear cycle can restart the session without restoring the preview layer. The standalone `PreviewLifecyclePolicy` test covers counters, but does not cover this real controller lifecycle defect. This fails criterion 12 / Requirement C and criterion 15's behavior-bearing boundary requirement.

## Criteria

- PASS: 1-10, 13-14, 16-19
- FAIL: 11, 12, 15, 20

## Required remediation

1. Wire camera authorization/session start outcomes into the real preview state/UI path. Denied, restricted, unavailable and error must be visible and must not be reported as running.
2. Make preview layer attachment/detachment symmetric across repeated appearance/disappearance. A reappearing controller must restore the preview layer before/with session restart without duplicating layers.
3. Add behavior-bearing tests for the lifecycle transition that currently fails and for authorization/error state mapping through a testable policy/adapter seam.
4. Preserve the existing narrow UIKit bridge, simulator no-fabrication behavior, NextLevel 0.19.1 pin and child scope.

PL-0069 remains unchecked.

Decision: **CHANGES_REQUIRED**
