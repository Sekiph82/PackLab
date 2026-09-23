# PL-0069 — Codex Remediation Work Order V05

Task: **PL-0069 — Preview bridge behavior-test closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CHATGPT_AUDIT_V04.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_PROMPT_V05.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CHATGPT_AUDIT_CRITERIA_V05.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_LOG_V05.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. PL-0070 remains accepted; PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M04.

Preserve all correct Batch-003 source. Fix only the remaining audit boundary.

## Mandatory remediation
1. Preserve the current authorization-before-start production logic and Settings-return recovery.
2. Introduce an injectable preview/session driver or equivalent seam actually used by NextLevelPreviewViewController so denied→authorized, start failure, and disappear→reappear transitions can be tested without a physical camera.
3. Add behavior tests that drive the real controller/lifecycle adapter seam, proving no false started state, exactly one attach/start after authorization, symmetric stop/detach, and visible error mapping.
4. Do not regress the current UIKit/SwiftUI bridge or simulator no-camera behavior.

Tests may use injected Apple-framework drivers/fakes and conditional compilation so they are reviewable on GitHub even when Windows cannot execute Xcode. Do not claim native execution unless actually run.

Create one implementation commit and one log-only commit. End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
