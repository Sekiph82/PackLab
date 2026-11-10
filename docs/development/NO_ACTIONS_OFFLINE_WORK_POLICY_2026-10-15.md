# PackLab | Zero-New-GitHub-Actions Work Mode | 15 October–31 October 2026

> **CURRENT OWNER DECISION: 2026-11-10 CLAUDE CODE EXCLUSIVE.** Claude, not Codex or ChatGPT, owns all new PackLab implementation, testing, independent peer-review coordination, GitHub Actions runs, `TASKS.md` updates and next-task selection. Earlier workflow texts below are dated history, not active stop/approval rules; genuine security, architecture, license, physical/owner/factory release gates remain binding. See root `CLAUDE.md`, `AGENTS.md`, `coordination/AUTONOMOUS_EXECUTION_POLICY.md`. 


> **HISTORICAL ONLY / SUPERSEDED ON 2026-11-04.** The owner has explicitly reauthorized GitHub Actions and continuous Codex task progression. The 2026-10-15 ban below is retained as dated evidence, not a current operational restriction. Current authority: root `AGENTS.md`, `TASKS.md` and `coordination/AUTONOMOUS_EXECUTION_POLICY.md`. Actual billing/runner limits and honest test/physical/legal gates remain.


**Owner decision, 2026-10-15.** GitHub Actions spending reported by owner: **USD 56.92 in approximately one week**, unacceptable. **No paid CI spending is approved.** The owner later authorized continuing work that does NOT use GitHub Actions through October, while hosted workflows remain paused. This note records that scope without altering approved PL-0354 acceptance.

## Hard boundary

1. **ZERO new GitHub Actions runs or reruns.** Do not dispatch, retry, rerun, enable, or deliberately trigger Actions jobs, even a supposedly free hosted minute. Do not authorize another CI provider, billing upgrade, spending-limit increase, payment or payment retry.
2. **No accidental automatic workflow launch.** As inspected on 2026-10-15:
   - `windows-python-quality.yml` push/main and PR filter: `.github/workflows/**`, `apps/windows-studio/**`, `core/**`, `pyproject.toml`, `tests/**`, `tools/**`, `uv.lock`.
   - `packlab-preview-windows.yml` push/main filter: `preview/windows/**`, its own workflow.
   - `packlab-capture-macos.yml` push/main or PR filter: `apps/ios-capture/**`, its own workflow.
   - Full native Windows build and other maintenance workflows require deliberate dispatch, but their trigger definitions must be rechecked before future pushes.
   **Safe routine main commits are confined to `docs/**`, `coordination/**`, root `TASKS.md`, and `AGENTS.md` if no other workflow trigger has been introduced.** Do not modify workflow files or CI-triggered source/test paths on main during the moratorium. A commit message alone (such as `[skip ci]`) is NOT the primary safety barrier.
3. **Source work, if authorized for a separate offline task, remains isolated on an owner-controlled PRIVATE non-main branch with NO pull request and NO GitHub Actions dispatch, or in a local protected checkout.** Verify the target branch and live workflow triggers before pushing. No PR, merging into `main`, or push to protected CI paths until the owner lifts the ban. Source work performed without hosted validation stays `UNVERIFIED_OFFLINE`, not `PASS`.
4. **PackLab task sequencing:** `PL-0354` full 205-test XCTest gate is **BLOCKED_NOT_RUN** on the final revision. Previous real 25/25 focused methods pass; prior 173/205 full run failed on earlier source. No PL-0354 acceptance, PL-0355 acceptance, M17 rollout or PL-0368 release. Preparatory work for later documentation/security/release tasks can proceed as `OFFLINE_PREPARATION_ONLY`, not audited task closure.
5. **Permitted no-Actions work:** source/documentation architecture review, small source-only security and version audits, pure-document preparation for PL-0359/0362/0363/0364/0365/0366/0367, safe synthetic test-case design, read-only issue triage, deterministic static checks on local machine that do not download/rebuild large native dependencies and respect owner disk budget. No Windows installer build, macOS test attempt, full native OCCT/OCP rebuild or expensive external provider.
6. **No automatic restart 2026-11-01.** November is the earliest time to reconsider, and only after the owner explicitly authorizes the next action. **Do not automatically resume paid Actions** on that date.
7. **No unexpected laptop disk usage:** avoid creating worktrees if possible; if a PackLab Codex task creates any, the persistent `AGENTS.md` safe non-forced end-of-task cleanup policy applies. Preserve OwnerDev, original Desktop, previous-good app/installer, R07 or other unique/dirty worktrees, private sample scans and source/evidence.
8. **GitHub artifact retention is not free by assumption.** Private accepted Windows Installer Actions artifact `11959245441` (due to expire **2026-12-14 08:38:33 UTC**) still exists. Previously reported active artifact inventory **4.873 GB** and storage billing/allowances are not independently confirmed. Do NOT delete it without owner approval and do NOT renew it using Actions during moratorium. Neither this plan nor documentation commits stops storage accrual.
9. Every offline change should state `ZERO_ACTIONS_DISPATCHED`, exact changed files, source/branch, checks actually run, limitations, no secret leakage and current blocked gates. No claims of full device/simulator/security validation from mere static checks. Formal redistribution legal review and Kenya factory distribution remain pending.

## Current frozen technical snapshot

| Item | Last authenticated evidence | Until resumed |
| --- | --- | --- |
| iOS Capture focused tests | Hosted macOS `38767357450`: 25/25 targeted passed, 0 skipped on `ce422ebf` | Preserve |
| Complete 205 XCTest suite | Earlier `38755083949`: 173 passed, 32 failed on old code; final run `38770566255` did not allocate a runner for billing restriction | **BLOCKED / NOT RECLASSIFIED** |
| Current R01 source | `4b1cf5168c6a2c461e4b31735763393c5ea0f53c`; log-only `3dd51193` | Freeze pending owner gate |
| Windows private Installer | Retained private artifact `11959245441`, expiration 2026-12-14 | Preserve, no forced renewal |
| Release/legal | `legal_review_required=true`, `public_release_authorized=false` | No release/factory rollout |

## Source of truth

This is an operating restriction and reference, **not a second task tracker**. Root `TASKS.md` is the only live project state, and root `AGENTS.md` governs Codex. The relevant historic audits are `PL-0354_CHATGPT_AUDIT_V02.md` and `PL-0353_CHATGPT_AUDIT_V02.md` in `coordination/sessions/M16-C001/`.
