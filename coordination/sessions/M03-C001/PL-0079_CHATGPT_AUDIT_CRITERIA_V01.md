# PL-0079 — ChatGPT Strict Audit Criteria V01

Task: **PL-0079 — Create ARKit world-tracking session without relying on LiDAR.**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CODEX_PROMPT_V01.md

All **20 criteria** are mandatory.

1. Root TASKS.md authorized M03-BATCH-001 / READY / CODEX before material work.
2. PL-0068 remains unchecked / OWNER_REQUIRED and this child does not fabricate or close that physical benchmark.
3. Repository synchronization is safe; no destructive reset/rebase/force-push/clean/stash of owner work is used.
4. Codex does not edit TASKS.md or ChatGPT audit artifacts.
5. Work stays inside M03 and does not start M04.
6. No secret, credential, provisioning private material, private Kenya scan/supplier asset or cache artifact enters public Git.
7. Changed files stay within the child scope plus justified minimal adjacent iOS/test/project files.
8. Existing iOS 17, Swift 6 strict concurrency, NextLevel 0.19.1, simulator fallback, diagnostics/privacy and PackScan contracts remain coherent.
9. The implementation materially satisfies the child mission: Create ARKit world-tracking session without relying on LiDAR.
10. Requirement A is satisfied: Implement ARWorldTrackingConfiguration using non-LiDAR world tracking only; do not require sceneDepth, mesh reconstruction or Pro-only sensors.
11. Requirement B is satisfied: Expose start/stop/state through the existing ARTrackingService seam with truthful unsupported/unavailable behavior.
12. Requirement C is satisfied: Configure only capabilities available on the iPhone 16 Standard baseline and guard ARWorldTrackingConfiguration support before starting.
13. Requirement D is satisfied: Keep AR session ownership/lifecycle isolated from SwiftUI and camera UI, avoiding duplicate ARSession creation.
14. Requirement E is satisfied: Add deterministic lifecycle/capability tests where possible and preserve simulator .unavailable behavior.
15. Positive, negative and boundary/state evidence is behavior-bearing rather than string-presence-only.
16. Existing accepted M01/M02 behavior relevant to the child remains unregressed.
17. Available tests/static/build validation are run truthfully; unavailable Xcode/device execution is reported rather than claimed.
18. `git diff --check` passes and builder `git diff -- TASKS.md` is empty.
19. The child Codex log exists, links prompt/criteria, records start/implementation/log commits, exact files, commands/results, limitations, privacy/signing review, remote visibility, and ends `READY_FOR_INDEPENDENT_AUDIT`.
20. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

Builder validation never self-closes this child. ChatGPT independently audits actual GitHub state after the milestone batch.
