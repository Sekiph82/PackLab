# PL-0036 — Codex Remediation Log V02

Task: PL-0036 — Current-state SwiftUI project revalidation after later repairs  
Repository: https://github.com/Sekiph82/PackLab  
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0036_CODEX_PROMPT_V02.md  
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0036_CHATGPT_AUDIT_CRITERIA_V02.md  
Prior audit evidence: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0036_CHATGPT_AUDIT_V01.md

## Scope and synchronization

- Root `TASKS.md` was read before material work and authorized the M01 remediation batch with Required Actor `CODEX`.
- Starting/current-state evidence commit: `3770cb1862c28c7cdb4a8353d99d2d98463cfd3b`.
- Synchronization: `git fetch origin main --prune`; `git rev-list --left-right --count HEAD...origin/main` returned `0 0`; `git status --porcelain` was empty before the evidence log was created.
- No reset, rebase, force-push, destructive checkout, stash, or clean operation was used.
- Root `TASKS.md` was not edited.

## Current-state remediation result

PL-0036 is an evidence-only revalidation cycle, as authorized by the V02 prompt. The current tree already contains the later PL-0040 plist repair and the PL-0037/PL-0043 project-graph remediations, so no implementation file was rewritten to manufacture a diff.

The final project state proves:

- PackLabCapture Debug and Release both use `GENERATE_INFOPLIST_FILE = NO` with `INFOPLIST_FILE = PackLabCapture/Info.plist`.
- `apps/ios-capture/PackLabCapture/Info.plist` exists, parses as XML, and contains the required application bundle keys.
- Product naming remains `PackLabCapture`, bundle identifier remains `com.packlab.capture`, minimum deployment remains iOS 17.0, and device family remains iPhone (`TARGETED_DEVICE_FAMILY = "1"`).
- The baseline documentation states that LiDAR and Pro-only hardware are not required.
- No personal team, signing identity, provisioning profile, credential, or private path is present in the project settings.
- The canonical NextLevel URL and exact `0.19.1` pin remain intact, with the product linked into the app Frameworks phase.
- The hosted test target retains its app dependency, source membership, `ENABLE_TESTABILITY`, `BUNDLE_LOADER`, `TEST_HOST=$(BUNDLE_LOADER)`, Swift 6, and complete strict-concurrency settings.

## Changed files

No implementation files were changed in this evidence-only child. The required file published by this child is:

- `coordination/sessions/M01-C001/PL-0036_CODEX_LOG_V02.md`

No adjacent files were required. No M02 work was started.

## Validation

Expected result: current project graph and plist strategy must be internally coherent, all baseline platform/package/test-target invariants must remain present, no protected or signing-sensitive material may be introduced, and no native macOS result may be claimed. A missing plist, inconsistent generation strategy, changed baseline, broken package/test graph, signing identifier, or `TASKS.md` diff would fail the checks.

Executed checks and actual results:

1. PowerShell current-state static revalidation for Debug/Release plist settings, plist existence/XML keys, product and bundle naming, iOS 17, iPhone family, no LiDAR/Pro-only requirement, no personal signing fields, NextLevel URL/pin/Frameworks link, hosted test wiring, test source/dependency, Swift 6 strict concurrency, and truthful platform boundary — all passed.
2. `git diff --check` — passed.
3. `git diff -- TASKS.md` — empty, as required.
4. `uv run pytest` — `39 passed, 1 deselected`.
5. `uv run ruff check core/src apps/windows-studio/src tools tests` — passed.
6. `uv run mypy core/src apps/windows-studio/src tools` — passed; no issues in 9 source files.
7. Exact-file/protected-file/privacy review — passed; no implementation diff, no secrets, private scans, supplier files, signing material, caches, or personal paths were added.
8. Native `xcodebuild`, simulator, signing, physical-device and camera validation — unavailable on this Windows checkout and not claimed.

The current-state evidence was already present at `3770cb1862c28c7cdb4a8353d99d2d98463cfd3b`; this child intentionally has no separate implementation commit.

## Publication and handoff

- Current-state checks were run after PL-0037, PL-0041, and PL-0043 had been published.
- The required evidence log is published in a separate commit from the current-state baseline.
- The log does not assign an audit verdict and does not predeclare its own commit SHA.

AWAITING_AUDIT
