# M16-C001-R08 V15 — ChatGPT Independent Audit V01

Date: 2026-10-09
Decision: **AUDITED_PARTIAL_CHANGES_REQUIRED**
Scope: R08 local disk hygiene implementation and handoff only; **PL-0350 V07 NOT STARTED**. This is not an M16 milestone PASS.

## Evidence inspected directly on GitHub main

- Implementation commit: https://github.com/Sekiph82/PackLab/commit/7d9db2ff14cbb94532b9703e04c9ea4dd708575f
- Safety correction: https://github.com/Sekiph82/PackLab/commit/49e1e165cd3b28faba021c5e788a2fe704e8aa25
- Final handoff correction: https://github.com/Sekiph82/PackLab/commit/90b8291dc8c5c0a4b2c74ff2c05e51891339e349
- Builder log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0350_V07_CONTINUATION_CODEX_LOG_V15.md
- Waste audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PACKLAB_DISK_OPTIMIZATION_REPORT_V15.md
- Implemented scripts: https://github.com/Sekiph82/PackLab/blob/main/tools/dev/run_packlab_tests.ps1 and https://github.com/Sekiph82/PackLab/blob/main/tools/dev/packlab_disk_hygiene.ps1
- Contract tests: https://github.com/Sekiph82/PackLab/blob/main/tests/ci/test_packlab_disk_hygiene_contract.py
- Original criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0350_V07_CONTINUATION_CHATGPT_AUDIT_CRITERIA_V15.md

This audit is independent GitHub source/diff review plus review of published builder evidence, **not** a reproduction of tests on the owner's Windows PC. Treat local run, Desktop EXE refresh, C: bytes, and process counts as builder-observed evidence, not independently rerun facts.

## Accepted partial implementation/evidence

1. Canonical main TASKS read and non-destructive worktree synchronization are documented (`AUTHORITY_SYNC_PASS`); owner dirty/unpublished work preserved.
2. New scripts and guidance establish explicit 40 GiB C: floor, 4 GiB pytest basetemp limit, 2 GiB per-fixture limit, 8 GiB disposable limit, unique test basetemp, candidate allowlist, dry run, and post-test cleanup.
3. Focused static contract checks: builder reports 3 passed, Ruff PASS, PowerShell parse PASS, diff checks PASS. No full regression was claimed.
4. Builder reports 0 post-task disposable PackLab bytes; C: free grew from 199,895,486,464 to 217,402,986,496 bytes across the work. This is not a proof of a particular deletion's physical reclaimed bytes.
5. OWNER DEV refresh on implementation commit 49e1e165 is recorded with 75,776-byte launcher and matching SHA-256; no new standalone installer or PL-0351 portability PASS is claimed.
6. The shared uv cache was NOT pruned while 59 consumers were using it. Skipping instead of terminating other apps or mutating their cache was the correct safety choice. Ambiguous legacy AppData OWNER DEV tree was preserved.
7. PL-0350 hosted builds, packaging clearance and later children were correctly not falsely marked complete.

## Mandatory findings (fix before R08 hygiene is AUDITED_PASS)

**F01 — 8 GiB monitoring only snapshots non-pytest roots.**
`run_packlab_tests.ps1` calls `Get-FixedPackLabDisposableBytes` once before starting pytest, then adds the dynamically rescanned `%TEMP%/PackLab/pytest` root. Concurrent growth in build/dist/staging/reports or OWNER DEV staging/temp is invisible to the per-poll 8 GiB check. Refactor to bounded refreshed accounting of ALL allowlisted disposable roots throughout the run, including updates after subprocess exit; fail closed on access/measurement errors. Keep scanning efficient and avoid unbounded full-cache walks.

**F02 — redirected stdout/stderr EOF can break monitoring.**
The live loop calls `Task.WaitAny` on a two-element array containing `$stdoutTask` and `$stderrTask` even after one task is set to `$null` at EOF. `Task.WaitAny` does not accept null entries, so an asymmetric stdout/stderr close may throw, skip continuing quota checks, and turn a valid run into a failure. Filter null tasks in the live loop and cover one-stream EOF / silent-process cases with a real executable regression.

**F03 — tests only assert source text, not quota behavior.**
The three tests inspect whether tokens such as `4GB`, `8GB`, `finally`, and `Stop-PytestTree` appear. No fault-injection/behavioral test proves an over-budget pytest subprocess is stopped, correct exit code emitted, basetemp removed, or unrelated running processes left alone. Add PowerShell integration/contract coverage with configurable tiny test-only thresholds and synthetic compact temporary files; **never allocate multi-GB fixtures**. Include healthy exit-code propagation, aborted-run cleanup, and error/locked-path behavior.

**F04 — original V15 full-gate not satisfied.**
Builder evidence records `uv_prune=SKIPPED_ACTIVE_CACHE_PROCESS`, 59 active consumers, and no before/after cache measurements, so V15 condition 20 is unmet. Do **not** stop unrelated Godot/Blender/MCP consumers or scan shared uv cache for 15+ minutes. Superseding V16 explicitly separates this external/shared-cache maintenance from PackLab's mandatory local test safety gate: record `DEFERRED_SHARED_UV_CACHE_ACTIVE` with consumer evidence; retry a supported `uv cache prune` only at a genuinely idle opportunity, with bounded measurement and results. A shared-cache deferral **must not block hosted PL-0350 CI architecture work** once PackLab safety fixes/pass are established. This is a changed authorized gate, not a claim that V15 passed.

**F05 — legacy AppData still unresolved, preserve until attributable.**
An earlier measurement found approximately 60,623,058,044 bytes under legacy AppData OWNER DEV; later it reappeared with ambiguous `logs`/`releases`. It is not included in the reported 0-byte disposable footprint (which excludes whole retained runtime roots). Produce a read-only per-directory inventory and prove which releases are unreachable/redundant before targeted cleanup. Do not treat the entire tree as disposable or recursively delete it, and do not bypass an automatic safety denial. Ambiguous/active content may remain under `DEFERRED_PROTECTED_UNVERIFIED` with truthful size and reason. Validate current and previous-good runtime survival.

## Disposition and next frontier

- R08 initial hygiene implementation: **PARTIALLY_ACCEPTED, remediation required**; not a task PASS.
- PL-0350 V07: **NOT_STARTED**. M16 accepted frontier remains PL-0347 V02 through PL-0349 V03.
- PL-0351 through PL-0367: **NOT_STARTED**. PL-0368: **DEFERRED_POST_M17**.
- Use the superseding V16 master prompt and criteria issued alongside this audit, then publish distinct corrected implementation/log/evidence. Preserve root TASKS.md as ChatGPT-only.
- No destructive workaround, process termination of unrelated applications, cache-force clean, or new 65 GiB test effort is authorized.

Verdict: `AUDITED_PARTIAL_CHANGES_REQUIRED`.
