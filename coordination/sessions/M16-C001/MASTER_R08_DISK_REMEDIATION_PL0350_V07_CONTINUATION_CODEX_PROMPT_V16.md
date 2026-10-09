# M16-C001-R08 — V16 Master: disk-budget behavioral remediation + shared-cache deferral + PL-0350 V07 continuation

Repository: https://github.com/Sekiph82/PackLab
Actor: CODEX
Authority: root `TASKS.md` on freshly fetched `origin/main`.
Supersedes the *next execution* section of V15 where it conflicts with this document. All V15 product/privacy/CI gates remain in force.
Independent R08 audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001-R08_CHATGPT_AUDIT_V01.md
Matching criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_R08_DISK_REMEDIATION_PL0350_V07_CONTINUATION_CHATGPT_AUDIT_CRITERIA_V16.md
Prior master to continue after remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_AUTHORITY_HARD_DISK_BUDGET_PL0350_V07_CONTINUATION_CODEX_PROMPT_V15.md

## Phase -1: non-destructive canonical preflight

Fetch `origin` and read `git show origin/main:TASKS.md`; confirm M16-C001-R08/V16 is authoritative, report `AUTHORITY_SYNC_PASS`. Preserve owner's dirty Desktop checkout, unpublished worktrees and all other projects; use an isolated managed worktree as needed. Never reset, delete or overwrite user work. Root TASKS.md and all CHATGPT_AUDIT files belong exclusively to ChatGPT and must NOT be modified by Codex. The old `PackLab.exe` remains usable.

## Phase 0: rectify audit findings F01–F05 before heavy local validation

1. **F01 aggregate budget:** in `tools/dev/run_packlab_tests.ps1`, refresh *all* defined PackLab disposable roots during the live loop, not just the pytest subtree; catch non-measurable/locked paths and fail closed with concise diagnostics, not success with zero. Keep 4 GiB pytest, 2 GiB single fixture, 8 GiB all-PACKLAB-disposable, and >=40 GiB free before heavy local work. Monitor C: free for rapid pressure. Implement efficient incremental/sampled or bounded scan so monitoring itself cannot run for many minutes while unchecked data grows. Do not enlarge limits. Guard race conditions and reparse points.
2. **F02 process output:** live `Task.WaitAny` must never receive `$null`; handle EOF on one stream, both streams, and no-output child processes while continuing budgets until all children exit. Preserve original healthy subprocess code. On cancellation/limit violations, stop only PackLab-owned launched process tree and remove the marked basetemp in `finally`; do not stop unrelated user processes.
3. **F03 behavioral tests:** write deterministic, safe Windows integration tests with injectable **tiny** limits (KiB/MiB scale only) using synthetic PackLab-owned temp trees. Prove normal success, propagated nonzero pytest code, 4 GiB *logic* triggered under test-only tiny threshold, 2 GiB fixture *logic*, concurrent growth of a non-pytest staging root crossing aggregate 8 GiB *logic*, asymmetric stdout/stderr completion, cleanup, child-process shutdown, and fail-closed measurement exception. Tests must never create multi-gigabyte payloads. Retain source-token tests only as supplement, not the acceptance evidence. Run focused tests first; use the wrapper for any larger suite; do not attempt a full suite until safety is proven.
4. **F04 uv shared-cache rule (explicit V16 override):** the 59 reportedly active uv-cache consumers are shared Godot/Blender/MCP processes, not PackLab-owned cleanup targets. Do not kill, ask to kill, disable, or move them; do not bypass permissions and do not run 15-minute recursive scans. If no consumers are active, use supported `uv cache prune` and collect bounded before/after evidence. If consumers still exist, record `DEFERRED_SHARED_UV_CACHE_ACTIVE`, count/sample/PIDs plus why, and *do not block PackLab hosted CI* solely for this reason. Use reasonably bounded/no-recursion cache size metadata when safe; otherwise explicitly say `NOT_MEASURED_ACTIVE_SHARED_CACHE`. NEVER represent this as a completed prune. No `uv cache clean`.
5. **F05 AppData:** measure read-only subdirectory sizes and identify legacy vs active runtime, manifests, exact owner, and other writers. Existing opt-in is not permission to delete the whole legacy AppData tree. Retain ambiguous `logs`/`releases`, active processes, current and previous-known-good runtime. Use exact candidate-specific allowlisted safe cleanup only where identity and unreachability are proven and security policy permits it, after dry-run; record `DEFERRED_PROTECTED_UNVERIFIED` for the rest. No blanket recursive deletion, policy bypass, owner-file deletion, or repeated deletion of a regenerating tree. Legacy retained bytes must not be mislabeled as 0 bytes of total disk usage; differentiate **measured disposable** vs **retained legacy**. Cleaning protected older data is not a PL-0350 hosted CI prerequisite.
6. Preserve no 65 GiB runaway: prove with tiny-limit behavioral checks; keep mandatory per-child bytes and cleanup summaries; track active retained worktrees without claiming they were deleted. Do not refactor unrelated product code.
7. Verify published scripts parse and tests pass; publish F01–F05 remediation log and direct evidence with explicit CI/local boundaries. After publication parity, use `tools/dev/post_codex_owner_dev_refresh.ps1` and verify Desktop native `PackLab.exe` identity/working launch without silently regressing UI; record whether it was actually opened and monitored. Keep obsolete `PackLab.lnk` absent.

**Phase 0 stopping rule:** if PackLab-owned safety/behavioral tests fail, stop, publish exact blocker, and do NOT start PL-0350. An unrelated actively used global uv cache and unverified legacy AppData are recorded as safe DEFERRED maintenance, not reasons to stop production CI.

## Phase A: PL-0350 V07 as originally specified

After Phase 0 remediation is demonstrably green, immediately continue **PL-0350 V07** using:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V07.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V07.md

Mandatory: dedicated controlled OCP/OCCT producer; `N_PROC=4`; exact-input sealed and verified runtime cache; cache MISS and cache HIT hosted proofs; separate packaging job never rebuilds OCP; zero unresolved redistribution/source/notice/forbidden Qt items; packaged QtPdf/OCP/Open3D smoke and a real cleared unsigned installer. Preserve all original fail-closed checks. Hosted CI does not depend on completing machine-wide uv pruning.

If PL-0350 V07 fails, publish the real blocker, its child log and master log with `BATCH_STOPPED_AT_PL-0350_V07`; stop, ending `AWAITING_MILESTONE_AUDIT`. Do not start PL-0351 without a green cleared installer.

## Phase B/C: conditional continuation, not early authorization to skip gates

If PL-0350 V07 is fully green, execute amended PL-0351 *clean-installed* Windows artifact proof (not OWNER DEV launcher proof). It must sanitize dev Python/site-packages/Qt/OCP/Open3D paths and prove QtCore loader + QtPdf + CAD + Open3D. If PL-0351 is green, continue PL-0352 through PL-0367 in exact order under the V15 master and individual existing prompts/criteria, with individual logs and publish/read-back parity. Do not start M17 or PL-0368 (DEFERRED_POST_M17). Owner-runtime refresh after every published implementation remains mandatory. No tag, release or signing without authorization.

## Completion protocol

Publish every implementation log and evidence to GitHub, never a local C: link as the handoff. Include exact tests/exits, SHAs, cache state and deferrals, owner runtime verification, free bytes before/after, aggregate disposable peaks and separate retained legacy size. Never claim Windows runtime validation you did not execute. Codex must NOT edit the auditor's files or root TASKS.md. Master log V16 location:
`coordination/sessions/M16-C001/MASTER_R08_DISK_REMEDIATION_PL0350_V07_CONTINUATION_CODEX_LOG_V16.md`.

If blocked: `BATCH_STOPPED_AT_<TASK>`. If completed through PL-0367: `BATCH_COMPLETED_PRE_M17_GATE`. Always end handoff with `AWAITING_MILESTONE_AUDIT`.
