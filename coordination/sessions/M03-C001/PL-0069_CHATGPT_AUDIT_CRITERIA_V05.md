# PL-0069 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-004 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED and PL-0070 remains accepted.
3. TASKS.md and ChatGPT audits are untouched by Codex; M04 is not started.
4. Prior Batch-003 passing behavior is preserved.
5. Previous audit PL-0069_CHATGPT_AUDIT_V04.md is fully addressed.
6. Preserve the current authorization-before-start production logic and Settings-return recovery.
7. Introduce an injectable preview/session driver or equivalent seam actually used by NextLevelPreviewViewController so denied→authorized, start failure, and disappear→reappear transitions can be tested without a physical camera.
8. Add behavior tests that drive the real controller/lifecycle adapter seam, proving no false started state, exactly one attach/start after authorization, symmetric stop/detach, and visible error mapping.
9. Do not regress the current UIKit/SwiftUI bridge or simulator no-camera behavior.
10. Behavior tests drive the actual production seam or an injected driver used by that seam, not a disconnected helper.
11. Relevant regressions/project checks and git diff --check are truthful and clean.
12. Child log records exact commits/files/results/limitations and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final main source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
