# PL-0109 — Codex Remediation Work Order V04

Task: **PL-0109 — Completion resume/recomputation integrity**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CHATGPT_AUDIT_CRITERIA_V04.md
Required child log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CODEX_LOG_V04.md

## Authorization

Before material work, root TASKS.md must authorize:
- Current Milestone: M04
- Current Task: M04-BATCH-004
- Current Task Status: READY
- Required Actor: CODEX
- PL-0109 unchecked
- all other 24 M04 children checked/accepted
- PL-0068 unchecked / OWNER_REQUIRED
- M05 not started

Otherwise stop `TASK_STATE_MISMATCH`.

Never edit TASKS.md or any ChatGPT audit file. Never start M05. Never fabricate PL-0068 evidence.

## Problem to fix

The current runtime persists a `CompletionDiagnostics` snapshot but does not persist/reconstruct the underlying required detail-pass state.

After resume, `restoreCompletion()` can make the UI look correct temporarily, while `m04DetailEvaluations` / detail coverage remain empty. A later accepted capture triggers `recomputeM04Completion()`, which can discard previously completed detail-pass evidence.

## Mandatory remediation

1. Preserve the current integrated M04 architecture. Do not introduce another camera, AR, motion, quality, coverage or session owner.
2. Persist the minimum authoritative detail-pass resume state needed to reconstruct completion, **or** reconstruct it deterministically from canonical accepted capture records.
3. The restored state must include enough information to reproduce required detail pass completion/missing status, not only a saved aggregate percentage.
4. A fresh `CaptureRuntimeViewModel` must rebuild/recompute `CompletionDiagnostics` from the restored authoritative state.
5. After resume, process at least one additional accepted capture that triggers `recomputeM04Completion()`; previously completed detail passes must remain completed.
6. Add explicit behavior for older sessions that lack the new detail-pass resume representation. Do not manufacture completion. Use truthful missing/unavailable state or deterministic reconstruction from canonical records.
7. Add a corrupt/inconsistent resume-state test that fails closed rather than inventing detail completion.
8. Preserve optional base pass unavailable/skipped semantics and existing asymmetric/turntable completion state.
9. Update the real ContentView/session-resume path if needed so it restores/reconstructs the new authoritative detail-pass state before normal capture resumes.

## Required tests

At minimum prove:
- mixed required detail passes: one complete, at least one missing;
- persisted state round-trip;
- fresh runtime restore/reconstruction;
- recomputed completion equals the pre-termination truth;
- an additional accepted capture after resume does not erase the earlier completed pass;
- legacy missing detail-state handling is truthful;
- corrupt/inconsistent detail-state handling is fail-closed;
- existing PL-0108 base skipped/unavailable behavior remains green.

Run:
- focused relevant tests;
- full declared locked suite;
- relevant project/static checks;
- `git diff --check`;
- protected-file/privacy/signing checks.

Native Swift/Xcode/iPhone results may be claimed only if genuinely executed.

## Commit/log discipline

Create one implementation/evidence commit.

Then publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CODEX_LOG_V04.md in a separate log-only commit.

Every user-facing repository reference must be a full GitHub URL, never a local path.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
