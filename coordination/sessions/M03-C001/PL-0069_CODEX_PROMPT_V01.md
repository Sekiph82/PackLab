# PL-0069 — Codex Work Order V01

Task: **PL-0069 — Integrate NextLevel preview into SwiftUI using a controlled UIKit bridge**

Repository: https://github.com/Sekiph82/PackLab
Previous open owner gate: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0068_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_PROMPT_V01.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_LOG_V01.md

## Authorization gate

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the accepted M01 iOS foundation state, the PL-0068 owner-required audit, this prompt and its criteria.

TASKS.md must show:
- Current Milestone: M03
- Current Sprint: M03-S01
- Current Task: PL-0069
- Current Task Status: READY
- Required Actor: CODEX
- PL-0068 still open / OWNER_REQUIRED
- Next Task/Action pointing to this V01 prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require a safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md or ChatGPT audit artifacts. Do not start PL-0070 or later M03 work.

## Existing foundation to preserve

The repository already has:
- SwiftUI app/root view;
- Swift 6 strict concurrency with warnings as errors;
- iOS 17 deployment target;
- NextLevel pinned exactly to `0.19.1`;
- `CameraService` abstraction;
- explicit simulator camera fallback;
- camera usage description;
- unit-test target.

Do not replace these foundations casually.

## Mission

Implement the first real PackLab Capture camera-preview integration.

Use NextLevel's actual preview/session contract behind a controlled UIKit boundary, then expose that boundary to SwiftUI. The SwiftUI layer should own presentation/state, while the UIKit/NextLevel adapter owns preview-layer/session attachment details.

The implementation must remain truthful on simulator and on devices where camera permission is denied/restricted/unavailable.

## Authorized primary scope

- `apps/ios-capture/PackLabCapture/**`
- `apps/ios-capture/PackLabCaptureTests/**`
- `apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj`

Minimal adjacent iOS documentation/config changes are allowed only when technically necessary and must be justified in the log.

## Mandatory behavior

1. Add a dedicated NextLevel-backed UIKit preview component suitable for embedding in SwiftUI.
2. Add the controlled SwiftUI bridge/container using `UIViewRepresentable`, `UIViewControllerRepresentable`, or an equivalently narrow UIKit bridge.
3. Keep NextLevel-specific preview/session details out of ordinary SwiftUI layout code.
4. Integrate the preview into the actual capture root UI so the app no longer shows only the bootstrap text screen.
5. Represent states such as loading/idle, running, denied/restricted, simulator/unavailable, and error truthfully.
6. Do not fabricate a camera image on simulator. A clear placeholder/status UI is correct there.
7. Avoid duplicate camera starts/stops when SwiftUI re-renders or the view repeatedly appears/disappears.
8. Make preview attachment/detachment and lifecycle ownership explicit enough to avoid an obvious retained preview/session cycle.
9. Preserve or coherently adapt `CameraService` and `SimulatorCameraService`; do not create two unrelated camera ownership systems.
10. Preserve the pinned NextLevel `0.19.1` dependency unless a concrete blocker is proven. Verify actual API usage against the pinned source rather than guessing from another release.
11. Keep this task limited to preview integration. Do not implement PL-0070 rear-camera enumeration/selection, PL-0071 still-photo capture, focus/exposure/WB controls, or later capture features.

## Validation

Run everything available and relevant in the builder environment:
- source/project membership checks;
- focused tests for state/lifecycle/fallback logic where feasible;
- Swift formatting/lint/static checks already supported by the repository;
- xcodebuild build/tests if macOS/Xcode is actually available;
- `git diff --check`;
- `git diff -- TASKS.md`;
- exact changed-file review;
- secrets/signing/private-asset review.

If native iPhone execution or xcodebuild is unavailable, report that truthfully. Do not claim a physical-device preview was observed unless it actually was.

## Handoff

Commit/push the implementation, then publish:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_LOG_V01.md

The log must include synchronized start, implementation commit, exact changed files, NextLevel API evidence/version, requirement mapping, validation commands/results, simulator/device limitations, privacy/signing review and remote visibility.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Stop. Do not self-audit and do not start PL-0070.
