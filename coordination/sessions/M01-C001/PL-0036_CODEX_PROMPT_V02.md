# PL-0036 — Codex Remediation Work Order V02

Task: **PL-0036 — Current-state SwiftUI project revalidation after later repairs**

Repository: https://github.com/Sekiph82/PackLab
Original/updated audit finding: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0036_CHATGPT_AUDIT_V01.md
This remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0036_CODEX_PROMPT_V02.md
Frozen remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0036_CHATGPT_AUDIT_CRITERIA_V02.md
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0036_CODEX_LOG_V02.md

## Authority

Root TASKS.md must authorize the M01 remediation batch and Required Actor CODEX. Read AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, coordination/AUDIT_POLICY.md, the relevant V01 prompt/criteria/log/audit history, and current files before work.

Before material work run:
- git fetch origin main --prune
- git rev-list --left-right --count HEAD...origin/main
- git status --porcelain

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md.

## Authorized files

- `apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj`
- `apps/ios-capture/PackLabCapture/Info.plist`
- `docs/development/IOS_BASELINE.md`

Minimal adjacent files are allowed only when technically necessary for the remediation and must be justified in the log.

## Mandatory remediation requirements

1. This is primarily a current-state revalidation task and must run after the other iOS project-graph remediations.
2. Prove Debug and Release now use a valid plist strategy: GENERATE_INFOPLIST_FILE/INFOPLIST_FILE settings must be internally coherent and the referenced plist must exist.
3. Revalidate PackLabCapture product/bundle naming, iOS 17 baseline, iPhone device family, no LiDAR/Pro-only requirement, and absence of personal signing/team identifiers.
4. Revalidate NextLevel package graph and test target changes have not broken the baseline project structure.
5. Do not rewrite files merely to manufacture a diff. If current state is correct, this child may be evidence/log-only.
6. Do not claim native Xcode/simulator/device evidence from Windows.

## Full regression

Re-run the original task's still-valid mandatory criteria, not only the named defect. Preserve all accepted behavior from sibling M01 tasks. Run task-relevant focused tests/checks, git diff --check, git diff -- TASKS.md, exact changed-file review, protected-file review and privacy/secrets review.

For Swift/Xcode tasks, static project/source evidence on Windows is allowed but native Xcode/simulator/device success must not be fabricated.

## Handoff

Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0036_CODEX_LOG_V02.md. Record synchronized start, implementation/evidence commit, exact files changed, defect-to-fix mapping, validation expected/failure/actual results, regressions, privacy/scope review, platform limitations and push evidence.

End with `AWAITING_AUDIT`. Do not self-audit. Do not start M02.
