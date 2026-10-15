# PL-0354-R01 | ONE-SHOT CODEX RECOVERY | 32 Failing iOS Simulator XCTest Cases

**Task remains PL-0354** in private `Sekiph82/PackLab`. The owner's handoff is truthful: **hosted simulator app build PASS, XCTest FAIL**. Proceed from the existing PL-0354 implementation; do NOT start PL-0355, M17, PL0368 or unrelated product features. There is no permission to waive tests to obtain green.

## Read first (authoritative)

- Live ChatGPT-owned root `TASKS.md`; permanent `AGENTS.md` mandatory safe task-created worktree removal rule.
- Independent auditor's actual hosted job-log review and failure families: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0354_CHATGPT_AUDIT_V01.md
- Original PL0354 V01 prompt, audit criteria and https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0354_CODEX_LOG_V01.md, including cleanup addendum.
- Actual failing macOS run: https://github.com/Sekiph82/PackLab/actions/runs/38755083949 at app revision `c9c0a1c66138c7cbd07bd889cf956fad415c96dd`; xcodebuild build PASS, 205 XCTest reported **173 passed, 32 failed**, overall failure. Do not mislabel as READY.
- Previous hosted run `38753546428`: 35 reported failures; do not assert all failures `pre-existing` without distinguishing baseline and compatibility edits.
- Checked-in Xcode project, shared scheme, `PackLabCaptureTests.swift`, affected Swift product code and original historical PL-xxxx contracts/audits for session integrity, camera, coverage and transfers.

## P0. Diagnose systematically, without changing acceptance

1. Retrieve full run **38755083949** log and hosted XCTest summary. If test result bundle is not uploaded, use available log assertions exactly; don't invent test diagnostics. Build a **32-case or assertion-family triage matrix** with actual test names, expected/actual, production modules and likely shared roots. Individual `Test Case failed` count can differ from the final `failedTests=32` summary due multiple assertions/reporting; record both forms truthfully.
2. Compare PL0354 Swift source changes with the pre-PL0354 commit and earlier test/contracts. Determine whether each failure is (A) compatibility-change regression, (B) genuine product logic defect, (C) invalid fixture/test setup, (D) simulator-only unavailable real camera behavior that should be correctly substituted by fake/injected service, or (E) unresolved. Do **not** call it pre-existing merely because first CI run failed.
3. Group by shared boundary and correct causes, NOT by changing expected assertions. Known concrete mismatches:
   - **Deletion/finalization/recovery:** expected `outsideRoot` vs `nonAuthoritative`; checksum/metadata binding errors vs `invalidManifest`; `interruptedWrite` rollback, `resumable` vs `corrupt_transaction`/missing record.
   - **Camera, runtime, pose:** continuous/locked focus observed as failed; accepted pose status nil, overlay not refreshing/epoch 0; pose stale vs available at boundary.
   - **Capture health/coverage:** acceptance `reject` vs `accept`, object fraction 0.09375 vs 0.125, middle vs upper elevation band boundaries, unexpected duplicate result, auto-capture backend call 0 vs 1, completion incomplete vs unavailable/nil.
   - **Preflight/share/transfer:** transparent preset failure, share missingPackage vs presenting/nil, wire decoder throws `unsupportedVersion`.
4. Confirm fixture source and products' invariants (security-first root traversal/symlink validation, checksums and manifest signing/binding, no insecure relaxation of data-integrity rules; accurate camera simulation, no bypassed health gate; wire protocol version cross-platform truth). If test expectation demonstrably contradicts frozen accepted spec, document it and preserve source of truth; don't quietly edit test to pass.
5. Do not alter NextLevel source/pin (still exact **0.19.1**), sign app, require Apple credentials, use private images/scans or attach/test on owner's iPhone. Any runner-local Swift language compatibility adjustment must remain exact and auditable.
6. First detect systematic root causes with smallest change sets. If proposed fix would materially re-design product behavior beyond restoring documented PL-xxxx contracts, **STOP with exact `OWNER_PRODUCT_DECISION_REQUIRED` and one narrow recommendation** rather than silently changing semantics.

## P1. Efficient implementation & tests

1. Work on **one clean, minimal Codex-managed PackLab worktree**; save locally only what is needed, no owner Desktop edits, no shared cache purge. Prefer GitHub-hosted macOS for actual Xcode tests; no Windows Installer/OCCT/OCP work. Respect previous actual C: free-space accounting and hard disk budgets.
2. Keep `.github/workflows/packlab-capture-macos.yml` fail-closed. Do not use `continue-on-error`, conditional skip list, `-skip-testing`, weakened XCTAssert/throw expectations, changed xcresult counting, `|| true`, or a separate superficial green workflow. All 205 original tests remain discoverable.
3. Correct proven product implementation bugs, or minimally repair **provably invalid synthetic test setup** only with documented original contract and a negative test protecting safety; preserve every important behavioral assertion. For every root cause, record original failing test + fix + protective regression. Avoid 32 arbitrary patches.
4. Add a **manual focused-test selection input** or a separately bounded targeted test invocation to run `xcodebuild test -only-testing:PackLabCaptureTests/PackLabCaptureTests/<testName>` (or grouped correct XCTest syntax) on hosted macOS. Optimize runner cost: test a few representative families/groups, not a full 205-test suite for every edit. Existing clean iOS Simulator 18.0/Xcode 16 image, pinned NextLevel 0.19.1, no signing. Upload only sanitized small text/error category if any, guarded by approved data-safety policy; no private media, xcresult data if unreviewed, signing info or giant derived-data artifacts.
5. The last phase MUST be **a real clean hosted macOS full suite** with every original 205 test discoverable and a green `xcodebuild test`, xcresult `result=Passed`, `failedTests=0`, job success. If fewer tests execute, compare discovery and explain legitimate count changes; no silent exclusion. Use bounded attempts, timeouts and proven stop conditions. A smoke build alone is not PASS.
6. Run scoped workflow validation, no-secret/privacy review, diff checks, and any relevant cross-platform fixture/protocol tests. If baseline changes after push, distinguish source HEAD from evidence SHA; no extra native or Windows build.
7. If the 32 failures cannot all be resolved without broad redesign or excessive Mac runner cycles, **publish truthful `BLOCKED_PRODUCT_BEHAVIOR` / `PARTIAL_XCTEST_FAILURES_REMAIN` with exact remaining test names**, and stop, instead of claiming success.

## P2. Publication and mandatory worktree cleanup

- Publish only authorized implementation and focused evidence to private `origin/main`. Include test matrix, before/after failed counts, full macOS Actions run/job URLs, implementation SHA and exact Xcode/simulator/provenance.
- Publish **separate append-only `coordination/sessions/M16-C001/PL-0354_CODEX_LOG_V02.md`** (do not falsify/overwrite V01's failed verification) after code and tests. End `READY_FOR_INDEPENDENT_AUDIT` only after real full macOS XCTest PASS; otherwise explain exact blocker with correct outcome.
- **Finish then clean:** after all tests, code+log pushed, remove each task-created clean/inactive/pushed PackLab local worktree via non-forced `git worktree remove` from a stable parent checkout. Verify no unique ignored/untracked/owner data, no active processes or outstanding commits, and preserve older dirty/unmerged R07/PL0350/PL0352/PL0353 worktrees and Desktop/OwnerDev. Never `--force`, `git clean -fdx`, blanket deletion or policy bypass. Record actual before/after C: free bytes, removed vs blocked, no false net disk recovery. If removal is blocked, stop cleanly and report it.
- Root `TASKS.md` **ChatGPT-only**. Never edit root task tracker or ChatGPT audits. Legal reviewer has NOT authorized factory distribution. No public release; repo remains PRIVATE.

**Execute independently from start to finish, avoiding needless owner questions and long unproductive CI loops.**
