# PL-0069 — ChatGPT Remediation Audit Criteria V03

Task: **PL-0069 — NextLevel preview / SwiftUI UIKit bridge remediation**
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CHATGPT_AUDIT_V02.md

All criteria mandatory.

1. M03-BATCH-002 / READY / CODEX authorization exists before material work.
2. PL-0068 remains unchecked / OWNER_REQUIRED.
3. PL-0070 accepted state is not regressed.
4. Codex does not edit TASKS.md or ChatGPT audit artifacts.
5. No M04 work starts.
6. No secrets/signing/private assets/caches enter public Git.
7. Child scope remains bounded to this remediation plus justified adjacent tests/project files.
8. Previously passing child behavior is preserved.
9. The previous independent audit is fully addressed.
10. Wire real camera authorization and NextLevel start/session failures into the preview state model; denied/restricted/unavailable/error must render visibly and must never be reported as running.
11. Make preview-layer attachment symmetric and idempotent across repeated viewDidAppear/viewDidDisappear cycles; reappearance must restore the preview without duplicate layers.
12. Keep one NextLevel/session owner behind the narrow UIKit bridge and preserve simulator no-camera behavior.
13. Add behavior-bearing tests for authorization/error mapping and disappear→reappear attach/start/stop transitions.
14. New tests are behavior-bearing and cover success, failure and boundary/state transitions.
15. Existing relevant M01/M02/M03 accepted contracts are unregressed.
16. Available validation is run truthfully; unavailable native execution is not claimed.
17. git diff --check and protected TASKS/audit checks pass.
18. Remediation log records exact commits/files/commands/results and maps prior failed criteria to evidence.
19. Actual GitHub source/diff/tests/log are mutually consistent and no material audit finding remains.

Closure requires independent ChatGPT AUDITED_PASS.
