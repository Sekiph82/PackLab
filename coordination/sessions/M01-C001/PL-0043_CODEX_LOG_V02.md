# PL-0043 — Codex Remediation Log V02

Task: PL-0043 — Hosted XCTest target wiring remediation  
Repository: https://github.com/Sekiph82/PackLab  
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_PROMPT_V02.md  
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_CRITERIA_V02.md  
Prior audit evidence: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_V01.md

## Scope and synchronization

- Root `TASKS.md` was read before material work and authorized the M01 remediation batch with Required Actor `CODEX`.
- Starting commit: `64ab469d70620d5b70fa2b4facab31f7dfb3b9d9`.
- Synchronization: `git fetch origin main --prune`; `git rev-list --left-right --count HEAD...origin/main` returned `0 0`; `git status --porcelain` was empty before edits.
- No reset, rebase, force-push, destructive checkout, stash, or clean operation was used.
- Root `TASKS.md` was not edited.

## Defect remediation

The prior audit found that the hosted XCTest target used `@testable import PackLabCapture` without source-controlled app testability and had `TEST_HOST` without `BUNDLE_LOADER`. The project graph now:

- enables `ENABLE_TESTABILITY = YES` in both the PackLabCapture Debug and Release app configurations;
- defines `BUNDLE_LOADER = "$(BUILT_PRODUCTS_DIR)/PackLabCapture.app/PackLabCapture"` in both test configurations;
- defines `TEST_HOST = "$(BUNDLE_LOADER)"` in both test configurations;
- preserves the existing PackLabCapture app target dependency, test source membership, Swift 6 settings, strict concurrency, and hardware-independent test source.

No personal `DEVELOPMENT_TEAM`, `CODE_SIGN_IDENTITY`, provisioning profile, credential, or private path was introduced. The baseline documentation records the graph wiring and keeps native Xcode validation as a future macOS/M16 boundary.

## Changed files

- `apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj`
- `docs/development/IOS_BASELINE.md`

No adjacent files were required. No M02 work was started.

## Validation

Expected result: static checks must find app testability in both configurations, coherent bundle-loader/host settings in both test configurations, test source membership, app dependency, strict concurrency, no personal signing fields, truthful platform-boundary wording, and no out-of-scope files. Any missing graph edge or privacy field would fail the checks.

Executed checks and actual results:

1. PowerShell static checks for Debug/Release `ENABLE_TESTABILITY`, Debug/Release `BUNDLE_LOADER`, `TEST_HOST=$(BUNDLE_LOADER)`, test source membership, app target dependency, strict concurrency, absence of personal signing/provisioning fields, and the explicit native-validation boundary — all passed.
2. `git diff --check` — passed.
3. `git diff -- TASKS.md` — empty, as required.
4. Exact changed-file review — passed; only the two authorized files changed.
5. Privacy/secrets review — passed; no credentials, private scans, supplier files, signing material, caches, or personal paths were added.
6. Native `xcodebuild test`, simulator, signing, physical-device and camera execution — unavailable on this Windows checkout and not claimed.

The implementation commit is `a63601955620e146c1634921fd6e17cbf6ecc328`.

## Publication and handoff

- Implementation commit pushed to `origin/main`: `a63601955620e146c1634921fd6e17cbf6ecc328`.
- After the implementation push, `git fetch origin main --prune` completed and `git rev-list --left-right --count HEAD...origin/main` returned `0 0`.
- This log is a separate evidence commit from the implementation commit.
- The log does not assign an audit verdict and does not predeclare its own commit SHA.

AWAITING_AUDIT
