# M16-C001-R08 - AUTHORITY SYNC + HARD DISK BUDGET / AUTO-CLEANUP + PL-0350 V07 + PL-0351→PL-0367 Master V15

Milestone: **M16 - CI/CD, Signing & Distribution**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Accepted frontier:

- PL-0347 V02: AUDITED_PASS
- PL-0348: AUDITED_PASS
- PL-0349 V03: AUDITED_PASS
- OWNER DEV native Desktop `PackLab.exe`: working/accepted for owner use

Current child:

- **PL-0350 V07 — dedicated controlled OCP runtime producer + verified reusable cache + packaging closure**

Then, only if green:

- **PL-0351 V01 — clean-installed artifact portability / QtCore loader gate**
- **PL-0352 through PL-0367 — ordered M16 continuation**
- **PL-0368 remains DEFERRED_POST_M17**

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V09.md

PL-0350 V07 prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V07.md

PL-0350 V07 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V07.md

PL-0351 prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CODEX_PROMPT_V01.md

PL-0351 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CHATGPT_AUDIT_CRITERIA_V01.md

Master criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0350_V07_CONTINUATION_CHATGPT_AUDIT_CRITERIA_V15.md

Required master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0350_V07_CONTINUATION_CODEX_LOG_V15.md

## Phase -1 - CANONICAL AUTHORITY SYNC / STALE-WORKTREE RECOVERY

This preflight is mandatory before all other phases.

A prior Codex attempt stopped because it claimed GitHub `TASKS.md` still showed an old M10 continuation. Independent GitHub API inspection proves that statement was stale/incorrect.

Canonical remote facts at prompt publication:

- repository: `Sekiph82/PackLab`
- branch: `main`
- canonical remote HEAD at publication: `e44c289aea5e9722b21807143d5f7eba318de62e`
- canonical `TASKS.md` blob SHA at publication: `7d8b54a59b2de1de4ec6c147c35b6d09234dfba0`
- canonical Project Status:
  - Current Milestone: `M16`
  - Current Sprint: `M16-C001 — CI/CD, Signing & Distribution`
  - Current Task: `M16-C001-R08 — permanent local disk hygiene/auto-cleanup first, then PL-0350 V07 ...`

### Authority source order

For tracker authority, use this order:

1. fetched Git remote ref `origin/main`;
2. `git show origin/main:TASKS.md`;
3. GitHub repository file API for `TASKS.md?ref=main`;
4. normal GitHub blob page.

Do **not** use a cached `raw.githubusercontent.com` response, browser cache, old local file, old worktree checkout, or previously copied TASKS text as authority.

### Required commands/evidence

Before implementation:

1. record current worktree path and `git status --porcelain`;
2. run `git fetch --prune origin`;
3. resolve and record `git rev-parse origin/main`;
4. read canonical tracker with:
   `git show origin/main:TASKS.md`;
5. verify the Project Status block authorizes M16-C001-R08 and this V15 master;
6. verify this master file and its criteria exist on `origin/main`;
7. only then synchronize the managed Codex checkout non-destructively.

### Non-destructive sync rule

If the current Codex worktree contains local changes:

- do not reset/delete them;
- inspect whether they are already published/reachable from origin/main;
- preserve unpublished work;
- if necessary create/use a clean managed worktree from current origin/main for this task;
- never overwrite owner-local Desktop PackLab work.

If local `TASKS.md` differs from `git show origin/main:TASKS.md`, treat the local copy as stale until proven otherwise.

### Moving-head rule

The publication SHA above is only a verification anchor, not a demand to pin forever.

If `origin/main` has advanced after V14 publication:

- read the newer remote `TASKS.md`;
- if it still authorizes M16-C001-R08/V15 or a clearly newer superseding continuation, follow the newer canonical tracker;
- if it changes the active task away from this scope, stop truthfully and report `CANONICAL_TASK_CHANGED`.

Do not stop merely because `origin/main` is newer than the publication SHA.

### Authority success marker

Record in the master log:

- `canonical_origin_main_sha`
- `canonical_tasks_blob_sha`
- `canonical_current_milestone`
- `canonical_current_task`
- `local_worktree_path`
- `local_worktree_status`
- `AUTHORITY_SYNC_PASS`

Only after `AUTHORITY_SYNC_PASS` may Phase 0 disk hygiene begin.

## Start rule

1. Synchronize the managed Codex checkout non-destructively with latest `origin/main`.
2. Preserve owner-local work and unrelated worktrees.
3. Read live root `TASKS.md`; it must authorize M16-C001-R08 / PL-0350 V07.
4. Read partial audit V09, V06 audit, V07 prompt and criteria.
5. Preserve the working native Desktop `PackLab.exe`.
6. Do not edit root `TASKS.md`.
7. Do not start M17 or PL-0368.

## Phase 0 - HARD LOCAL DISK BUDGET + OPTIMIZATION + AUTO-CLEANUP CONTRACT

This phase is mandatory before any more local test/build work and remains a standing PackLab engineering rule.

The product is expected to be on the order of a few GB, not tens of GB. A local test run consuming 65 GB is a test-infrastructure defect.

**Do not solve disk pressure by asking the owner to delete personal files.**
Optimize PackLab development first, then delete PackLab-generated disposable data.

### 0.1 Protected owner data

Never auto-delete:

- owner Videos, Pictures, Documents, Downloads, OneDrive or unrelated Desktop content;
- PackLab Git source;
- dirty/unpublished/active worktrees;
- Desktop `PackLab.exe`;
- active OWNER DEV runtime and launcher;
- one previous-known-good OWNER DEV runtime;
- unresolved evidence explicitly referenced by an active task;
- unrelated application/model/browser caches.

No broad recursive deletion outside allowlisted PackLab-generated locations.

### 0.2 PackLab local disk budget

Enforce these hard budgets for local development:

- **40 GiB minimum free C:** before any heavy operation;
- **4 GiB maximum pytest basetemp per full local test run**;
- **8 GiB maximum total disposable PackLab temp/build/staging footprint** at any one time, excluding the active Git worktree and protected OWNER DEV current+previous-good runtimes;
- **2 GiB maximum single generated test fixture/tree** unless a specific test has a written justification and dedicated cleanup;
- after each child handoff, **completed disposable footprint target = <1 GiB**.

If any hard limit is exceeded:

1. stop the responsible local test/build;
2. identify the top growth paths;
3. optimize the test/build implementation;
4. cleanup only PackLab-generated disposable data;
5. rerun only after the footprint is back under budget.

Do not merely increase the budget.

### 0.3 Eliminate pathological test copying

Audit the PackLab test suite for disk-amplifying behavior.

Forbidden patterns unless explicitly justified:

- recursively copying the whole PackLab repository into `tmp_path`;
- copying `.venv` into test temp;
- copying OWNER DEV runtimes into each test case;
- copying package caches into fixtures;
- cloning the full repo repeatedly for tests that only need a few files;
- materializing multi-GB fake assets when sparse/minimal fixtures would test the same behavior;
- retaining per-test build/install trees after assertions complete.

Refactor tests to use:

- minimal synthetic fixtures;
- shared read-only session fixtures when isolation does not require duplication;
- targeted file subsets;
- sparse files for byte-size/path behavior when file contents are irrelevant;
- small deterministic sample assets;
- in-memory data where practical;
- explicit cleanup in fixture finalizers.

A full test suite must not scale disk consumption linearly with test count by duplicating the same runtime/repository.

### 0.4 Full pytest wrapper with live quota enforcement

Implement a checked-in wrapper, e.g.:

`tools/dev/run_packlab_tests.ps1`

All full local pytest runs must use it.

Required behavior:

1. run disk preflight;
2. create one unique PackLab-owned `--basetemp`;
3. start pytest as a child process;
4. poll basetemp size while pytest is running;
5. if basetemp exceeds **4 GiB**, terminate pytest cleanly and fail with:
   `PYTEST_DISK_BUDGET_EXCEEDED`;
6. print the largest subdirectories/files responsible;
7. preserve only compact text/JSON diagnostics;
8. delete the basetemp in `finally`;
9. preserve pytest's original exit code when the disk quota did not trigger;
10. run post-test hygiene.

The wrapper must make another 65 GB runaway impossible.

### 0.5 Historical pytest cleanup

Inventory `%TEMP%\pytest-of-sekip` and any PackLab-specific pytest temp roots.

Before removal:

- prove no active pytest/mypy/test Python process owns them;
- exclude the current run;
- delete stale completed PackLab pytest directories;
- report locked paths individually.

Desired steady state:

- no completed PackLab pytest run tree remains;
- only the currently executing basetemp may exist.

### 0.6 PackLab AppData / OWNER DEV cleanup

Inventory PackLab-owned generated locations including, where present:

- `%LOCALAPPDATA%\PackLab`;
- `C:\Users\sekip\Desktop\PackLab\OwnerDev`;
- PackLab staging/temp/log/release subdirectories.

Delete only unused generated material proven safe:

- superseded OWNER DEV releases beyond current + one previous-good;
- failed/incomplete staging directories;
- abandoned refresh temp directories;
- obsolete generated manifests superseded by current runtime;
- completed temporary installer/test staging;
- old startup/runtime logs beyond retention.

Retention:

- current OWNER DEV runtime;
- one previous-known-good;
- stable launcher;
- newest 20 logs, and normally no logs older than 7 days;
- explicitly preserved unresolved failure evidence.

Never delete active runtime files in use by the open PackLab Studio process.

### 0.7 Build/staging cleanup

Local reproducible build products must have task-scoped lifetimes.

Immediately remove after required evidence is retained:

- PyInstaller work/dist/stage directories;
- local OCP/OCCT extracted source/build/install trees;
- temporary installer input/output;
- temporary source archives;
- one-off test virtual environments;
- generated fixture copies;
- temporary screenshot/video/test diagnostic assets.

Prefer hosted CI for the heavy controlled OCP/OCCT source build. Do not reproduce the multi-hour OCP build locally unless the task specifically requires a focused local diagnostic that cannot be done hosted.

### 0.8 Codex worktree budget

The Codex worktree area previously reached tens of GB.

At each task end:

1. `git fetch --prune origin`;
2. `git worktree list --porcelain`;
3. examine every PackLab Codex worktree;
4. remove only worktrees that are:
   - clean;
   - inactive;
   - fully published/reachable from remote;
   - not owner-created;
   - not needed for the current task;
5. use `git worktree remove`, then `git worktree prune`.

Dirty/unpublished/active worktrees stay.

However, do not allow abandoned clean worktrees to accumulate indefinitely.

### 0.9 Cache policy

Caches exist to save time, not consume the disk without bound.

After every major local validation:

- run `uv cache prune`;
- record uv cache bytes before/after.

If pip cache exceeds 2 GiB:

- reduce it using supported `pip cache` commands.

Do not routinely use `uv cache clean`.
Do not manually delete installed Python interpreters or active virtual environments.

Do not auto-delete Hugging Face, Puppeteer, Codex runtime or unrelated application caches.

### 0.10 Permanent disk-hygiene helper

Implement a checked-in helper, e.g.:

`tools/dev/packlab_disk_hygiene.ps1`

Required modes:

- `inventory`
- `preflight`
- `post-test`
- `post-task`

Required properties:

- explicit allowlist;
- protected-root denylist;
- dry-run;
- candidate list before deletion;
- per-category byte accounting;
- safe handling of locked/access-denied paths;
- no administrator requirement;
- no broad user-profile deletion;
- machine-readable JSON summary option.

### 0.11 Test-suite disk optimization audit

Before running the next full suite, inspect current tests for the top disk-producing fixture patterns.

Create a focused report under the current coordination session containing:

- top fixture/test creators of temp bytes;
- whether they copy repo/runtime/.venv/build trees;
- before/after expected footprint;
- optimization applied.

Fix the pathological creators before accepting the hygiene task as complete.

A cleanup script alone is not sufficient. The generator of the waste must be corrected.

### 0.12 First-pass cleanup acceptance

Before PL-0350 V07 heavy work resumes:

- stale completed PackLab pytest temps are gone;
- safe unused PackLab AppData/OWNER DEV staging/release/log leftovers are cleaned;
- safely removable completed Codex worktrees are retired;
- uv cache prune is complete;
- current+previous-good OWNER DEV remain intact;
- personal files are untouched;
- C: free space is recorded;
- current disposable PackLab footprint is measured;
- no known PackLab disposable category is above its hard budget.

### 0.13 Per-child cleanup gate

Before every child log:

- run `post-task`;
- record:
  - disk_free_before_bytes
  - disk_free_after_bytes
  - reclaimed_bytes
  - pytest_temp_peak_bytes
  - disposable_packlab_peak_bytes
  - cleanup bytes by category
  - retained worktrees + reasons
  - locked paths
  - budget violations, if any

A child cannot hand off as green with an unexplained multi-GB disposable tree left behind.

### 0.14 Optimization principle

If a PackLab operation can be made cheaper by reuse, caching, minimal fixtures, hosted CI, targeted tests, or avoiding duplicate copies, **optimize first**.

Deletion is the safety net, not the primary design.

Only after Phase 0 passes may PL-0350 V07 continue.

## Phase A - PL-0350 V07

Execute PL-0350 V07 exactly.

Required architecture:

- dedicated controlled OCP runtime producer job;
- explicit OCP bindgen `N_PROC=4`;
- sealed runtime bundle;
- exact cache key from native build inputs;
- fail-closed cache validation;
- same-run runtime artifact transfer;
- separate packaging job that never rebuilds OCP/OCCT;
- unchanged packaged capability and redistribution gates.

If V07 remains blocked:

- publish implementation/evidence;
- publish exact hosted blocker evidence;
- publish `PL-0350_CODEX_LOG_V07.md`;
- verify local/origin/GitHub parity;
- refresh OWNER DEV native Desktop EXE;
- publish/update the master log;
- record `BATCH_STOPPED_AT_PL-0350_V07`;
- end exactly `AWAITING_MILESTONE_AUDIT`;
- stop.

Do not start PL-0351.

If V07 is builder-green, it must have:

- first cache-miss controlled runtime build completed within hosted job limit;
- second run/rerun verified controlled-runtime cache HIT with no pywrap rebuild;
- zero unresolved shipped files/components;
- zero missing notices/source packages;
- zero forbidden Qt components;
- fresh packaged Qt/PDF/OCP/Open3D smoke PASS;
- cleared versioned unsigned installer artifact.

Then continue immediately to PL-0351.

## Phase B - PL-0351 clean installed-artifact portability

Execute the existing amended PL-0351 V01 prompt/criteria.

Mandatory:

- separate fresh Windows job;
- download exact cleared PL-0350 installer artifact;
- verify SHA-256 and byte length;
- install into isolated path;
- sanitize repository/.venv/Python/Qt/Shiboken/OCP/Open3D developer paths;
- launch the installed `PackLabStudio.exe`;
- require real Qt GUI + QtPdf + OCP/CAD + Open3D capability smoke;
- fail hard on DLL load/procedure/entry-point/ICU/plugin/Shiboken/architecture errors;
- cleanup/uninstall even on failure.

This remains the permanent installed-artifact regression gate for the previously observed QtCore missing-procedure failure and for the fact that OWNER DEV currently relies on an external base Python installation.

If PL-0351 fails:

- publish exact GitHub-hosted evidence;
- publish child log;
- stop;
- do not start PL-0352.

If green, publish child implementation/evidence + distinct child log and continue.

## Phase C - PL-0352 through PL-0367

Execute existing authorized child prompts/criteria in exact order:

PL-0352 → PL-0353 → PL-0354 → PL-0355 → PL-0356 → PL-0357 → PL-0358 → PL-0359 → PL-0360 → PL-0361 → PL-0362 → PL-0363 → PL-0364 → PL-0365 → PL-0366 → PL-0367.

For each completed child:

- implement only authorized scope;
- run required validation;
- publish implementation/evidence;
- publish distinct child Codex log;
- verify local/origin/GitHub parity;
- refresh OWNER DEV native Desktop EXE;
- continue automatically while hard gates remain green.

Do not wait for intermediate ChatGPT audit.

## GitHub-link handoff contract

Every Codex owner handoff must use clickable GitHub HTTPS links.

For every applicable child/master handoff include:

- prompt;
- audit criteria;
- implementation commit(s);
- evidence commit(s);
- child Codex log;
- master Codex log;
- GitHub Actions quality run;
- GitHub Actions runtime-producer/build/test runs;
- GitHub Actions artifacts.

Do not provide local `C:\...` paths as owner handoff references.

Published logs must likewise use GitHub URLs for referenced repository files/runs/artifacts wherever practical.

## OWNER DEV native Desktop EXE standing rule

After each published implementation/evidence commit and verified parity:

- refresh OWNER DEV;
- verify real Desktop `PackLab.exe`;
- keep obsolete Desktop LNK absent;
- do not regress to PowerShell launch;
- record `OWNER_DEV_EXE_READY`.

## Retained hard gates

- no private scan/supplier/project data, credentials, checkpoints or signing material in public Git/artifacts;
- default iOS path remains unsigned/secret-free;
- no Git tag/GitHub Release/V0.1 before PL-0368;
- PL-0368 remains `DEFERRED_POST_M17`;
- M17 must not start.

## Stop conditions

Stop on any real:

- controlled runtime producer timeout;
- cache provenance/validation ambiguity;
- source/package hash mismatch;
- packaged capability regression;
- redistribution/source/notice blocker;
- installed-artifact loader failure;
- artifact provenance mismatch;
- privacy/secret leak;
- signing/release ambiguity;
- owner-required decision;
- need to start PL-0368 or M17.

## Mandatory final disk hygiene

Before the final master handoff, run the permanent `post-task` disk hygiene one last time.

The final master log must include aggregate local disk-hygiene evidence across the batch and confirm:

- no completed PackLab pytest basetemp remains;
- no known completed/published removable Codex PackLab worktree remains;
- no stale local build/staging/source-extraction tree remains;
- uv cache prune completed;
- OWNER DEV retention is bounded;
- C: free-space floor is satisfied or a truthful disk blocker is recorded;
- no personal owner file was deleted.

## Handoff

Required master log:

`coordination/sessions/M16-C001/MASTER_PL0350_V07_CONTINUATION_CODEX_LOG_V15.md`

If blocked, record `BATCH_STOPPED_AT_<TASK>` and end exactly:

`AWAITING_MILESTONE_AUDIT`

If PL-0350 V07 through PL-0367 all become builder-green, record:

`BATCH_COMPLETED_PRE_M17_GATE`

and end exactly:

`AWAITING_MILESTONE_AUDIT`

Final owner-facing response must use GitHub HTTPS links only.
