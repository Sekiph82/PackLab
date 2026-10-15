# PL-0354 | ChatGPT Independent Audit V01 | macOS iOS Simulator CI (2026-10-15)

**VERDICT: AUDITED_PARTIAL_CHANGES_REQUIRED — HOSTED BUILD PASS; XTEST FAIL (205 total, 173 passed, 32 failed). PL-0354 STAYS OPEN.**

The Codex handoff correctly **did not** declare `READY_FOR_INDEPENDENT_AUDIT`. This independent review checked private GitHub source, final builder log, actual GitHub Actions run/job metadata and the full hosted job log. There is no basis to mark macOS test acceptance green until all required tests pass. A failed workflow that correctly propagates failures is a positive CI-safety result, not completion of the Swift XCTest acceptance gate.

## Independently verified

- Live repo `Sekiph82/PackLab` confirmed **PRIVATE**. Initial `main=7b13618ecfa335cccb22450b2a9a9bf3b73e4fb1`; the final `7b13618` commit changed only `PL-0354_CODEX_LOG_V01.md`. Implementation source revision `c9c0a1c66138c7cbd07bd889cf956fad415c96dd`.
- Latest run https://github.com/Sekiph82/PackLab/actions/runs/38755083949: `push` at exact implementation revision; job `116491265439`, `macos-15`, overall **FAILURE**. Checkout, Xcode provenance, iOS 18.0 runtime, NextLevel dependency resolution, and **unsigned** Xcode Simulator **app build** all **SUCCESS**. `Run PackLabCaptureTests` and `Verify and record XCTest summary` correctly failed.
- Hosted XCTest JSON summary actually printed `result=Failed`, `totalTestCount=205`, `passedTests=173`, `failedTests=32`. Thus **32 failed tests according to final xcresult summary**. Do not rely on the number of individual `Test Case failed` lines or failed assertion messages as the definitive count; multiple failure messages can occur in individual XCTest cases.
- Existing `.github/workflows/packlab-capture-macos.yml`: `CODE_SIGNING_ALLOWED=NO`, `CODE_SIGNING_REQUIRED=NO`, empty `CODE_SIGN_IDENTITY`; `macos-15`, Xcode_16, iPhone 16/iOS 18.0 simulator, `contents: read`, bounded 45 min, push/main+path-scoped PR+dispatch; fail propagation via `set -euo pipefail`, `xcodebuild test | tee` and separate xcresult summary gate. No signing secrets or workflow product artifact upload.
- Shared Xcode scheme and app plist executable metadata were added to allow the real test run. NextLevel remains pinned to **0.19.1**, though the workflow applies a **runner-local compatibility rewrite** of that resolved dependency's Package.swift Swift language mode. Any future work must retain explicit provenance and verify true package compile/test semantics, not silently loosen upstream code.
- Codex reports no Owner Desktop, `TASKS.md`, Windows Installer, OCCT/OCP, M17 or PL-0355 changes; the source diff concerns existing iOS app/test Swift compile compatibility, Xcode project/scheme/plist and the new CI workflow. The independent auditor did not have the owner laptop filesystem and did not personally verify desktop paths.
- Previous hosted run `38753546428` also reached tests but had 35 failures; latest 32 failures is **improvement, not green**. Cannot assume all failures predated PL-0354: CI first exposed them, and some test/Swift implementation compatibility edits occurred in PL-0354. Compare baseline, prior source contracts and current implementation before identifying cause.

## Evidence-based failure families

From full hosted job log, exact examples (not exhaustive):
- **Session integrity/deletion/recovery/finalization:** `testAuthoritativeDeletionRemovesSessionAndRejectsTraversal`, `testDeletionPlanRequiresConfirmationAndStaysInsideRoot`: expected `outsideRoot`, actual `nonAuthoritative`. `testFinalizationGateDistinguishesBindingAndChecksumFailures`: expected `checksumFailure` / `invalidMetadataBinding`, actual `invalidManifest`. `testPL0088...` catches `interruptedWrite`; `testPL0090...` expected `resumable`, actual `blocked(corrupt_transaction)`; session discovery returns `blocked(missing_or_corrupt_record)`.
- **Camera/focus, AR pose & runtime sampling:** `testPL0073FocusCannotLockBeforeObservedStabilization` expected `continuous` / `locked`, actual `failed`; `testPL0080AndPL0081...` pose status missing; `testPL0083AndPL0085...`, `testPL0085Overlay...`; `testPoseClockBridge...` expected `stale`, actual `available`.
- **Capture transactions and auto-gating:** `testPL0089RetakeCallbackAndDeleteRetakeFailureStagesRollbackCoherently` repeated rollback assertion failure; `testPL0104ProductionAutoCapture...` backend request expected 1, actual 0; production gate matrix mismatch.
- **Coverage, duplicate detection & completion:** `testPL0095...` `reject` vs `accept`, `testPL0097...` `0.09375` vs `0.125`; `testPL0102...` and `testPL0106...` elevation ring boundary `middle` vs `upper`; `testPL0105...` duplicate detector; `testPL0109...` `incomplete` vs `unavailable`, nil completion diagnostics.
- **Preflight, sharing, transfer model:** `testPL0118...` fails transparent preflight preset; `testPL0120...` expected `missingPackage` / `PackScanShareError.missingPackage`, actual presenting/nil; `testPL0121SwiftWireModelsMatchSharedGoldenFields` throws `unsupportedVersion`.

These are **behavior/contract mismatches exposed by real simulator CI**. They may share causes (state lifecycles, test fixture validity, ordering/clock boundaries, Swift migration semantics), so do not infer 32 unrelated defects or weaken expectations blindly.

## New owner-mandated worktree closure

The builder log records ONE PL-0354-created worktree `codex/pl-0354-macos-ci`, clean, merged/pushed and free of unique files; removed via ordinary `git worktree remove` without `--force`. Three previous/other PackLab task worktrees with unpublished commits and thousands of ignored environment/cache records were **correctly preserved**, as were R07/OwnerDev entries. C: free before `97,186,861,056` bytes, after `97,222,111,232`, **actual net increase 35,250,176 bytes (33.62 MiB)**. Logical file length is not substituted for measured free space. **This cleanup is builder-attested only**, since ChatGPT cannot directly inspect the user's laptop. Policy: https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md.

## Decision and required follow-up

**PL-0354 remains OPEN; PL-0355/M17 not started.** Use one scoped V02 repair/diagnosis prompt: read complete hosted failing test evidence, cluster failures, inspect pre-PL0354 source & original test semantics, implement minimal behavior fixes for genuine regressions (or correct explicitly proven invalid synthetic fixtures without diluting safety), run targeted macOS `-only-testing` subsets, then ONE bounded real full hosted xcodebuild test run once focused groups pass. Do NOT alter tests merely to make CI green, exclude/skip failing tests, ignore exit status, repin NextLevel or introduce signing. If original product contracts conflict or a substantive M09–M12 behavior/design change is necessary, stop with precise decision request rather than invent product behavior.

No new OCCT/OCP/Windows Installer build, disk cleanup or owner Desktop changes. Codex must honor mandatory cleanup of any **new task-created worktree after it has finished and published**, and separate cleanup result from XCTest acceptance.

**Next prompt:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0354_R01_SWIFT_XCTEST_FAILURE_RECOVERY_CODEX_PROMPT.md

**Formal flags:** `legal_review_required=true`; `public_release_authorized=false`; no factory deployment authorized.
