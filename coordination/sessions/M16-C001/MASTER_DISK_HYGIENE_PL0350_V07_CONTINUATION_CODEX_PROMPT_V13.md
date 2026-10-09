# M16-C001-R08 - DISK HYGIENE + PL-0350 V07 Controlled Runtime Cache + PL-0351 Clean Install + PL-0352→PL-0367 Continuation Master V13

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
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0350_V07_CONTINUATION_CHATGPT_AUDIT_CRITERIA_V13.md

Required master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0350_V07_CONTINUATION_CODEX_LOG_V13.md

## Start rule

1. Synchronize the managed Codex checkout non-destructively with latest `origin/main`.
2. Preserve owner-local work and unrelated worktrees.
3. Read live root `TASKS.md`; it must authorize M16-C001-R08 / PL-0350 V07.
4. Read partial audit V09, V06 audit, V07 prompt and criteria.
5. Preserve the working native Desktop `PackLab.exe`.
6. Do not edit root `TASKS.md`.
7. Do not start M17 or PL-0368.

## Phase 0 - PERMANENT LOCAL DISK HYGIENE / AUTO-CLEANUP CONTRACT

This phase is mandatory **before any more local regression/build work** and the cleanup rules remain mandatory after every child/task in this master.

The owner has already had to delete personal files because PackLab/Codex development left tens of gigabytes of reproducible temporary data on C:.

That is no longer acceptable.

This is **not** permission to perform broad deletion. Cleanup must be narrow, evidence-based, and limited to reproducible development artifacts.

### 0.1 Protected paths — NEVER auto-delete

Do not automatically delete, move, truncate, or overwrite:

- the PackLab Git checkout;
- any dirty or active Git worktree;
- `C:\Users\sekip\Desktop\PackLab.exe`;
- the active OWNER DEV runtime;
- the current OWNER DEV launcher;
- the one previous-known-good OWNER DEV runtime;
- `AppData\Local\PackLab` user/application data unless a specific subpath is proven to be disposable logs/staging under this contract;
- owner Documents, Desktop files other than specifically named PackLab-generated artifacts, Videos, Pictures, Downloads, OneDrive, or other personal folders;
- model/checkpoint/browser caches such as Hugging Face/Puppeteer unless separately authorized by the owner;
- Codex runtime/cache directories required by the currently running Codex process.

Never use a broad `Remove-Item C:\Users\sekip\... -Recurse` pattern.

### 0.2 Disk preflight

Before running any local full pytest, mypy+pytest batch, PyInstaller build, OCP/OCCT build, or other disk-heavy operation:

1. measure free bytes on C:;
2. inventory PackLab-generated disposable storage;
3. record sizes in a local-safe disk-hygiene report;
4. require at least **40 GiB free** before starting a heavy operation.

If free space is below 40 GiB:

- perform only the safe cleanup classes below;
- re-measure;
- if still below 40 GiB, stop with `LOCAL_DISK_SPACE_BLOCKED`;
- do not ask the owner to delete personal files.

### 0.3 pytest temporary files — immediate cleanup

The prior machine inspection found approximately **64.65 GB** under:

`%TEMP%\pytest-of-sekip`

This must not recur.

Implement a checked-in local test wrapper, for example:

`tools/dev/run_packlab_tests.ps1`

or equivalent, with this contract:

- every Codex/local pytest invocation uses a unique explicit `--basetemp` under a PackLab-owned disposable temp root;
- the wrapper records the path it created;
- test execution occurs inside `try/finally`;
- on success, the entire run temp directory is removed immediately;
- on test failure, preserve only compact text/JSON diagnostics needed for review, then remove large copied/build/generated test trees;
- do not retain multi-GB pytest temp trees merely for debugging;
- if a test needs an artifact retained, copy only the explicitly required small artifact into the child evidence area before cleanup.

Before deleting historical `%TEMP%\pytest-of-sekip\pytest-*` directories:

1. confirm no active pytest/mypy/test Python process owns the run;
2. exclude the current run basetemp;
3. remove only stale pytest-generated run directories;
4. tolerate Windows lock failures per-path and report them instead of broad-force deletion.

The desired post-test state is **no completed PackLab pytest run directory left behind**.

### 0.4 Build/staging/source-extraction cleanup — immediate cleanup

All locally generated reproducible heavyweight directories must be removed after the command/task that needs them has finished and required evidence has been copied/published.

Examples include:

- local PyInstaller `build/`, `dist/`, work dirs and staging trees created only for validation;
- extracted OCP/OCCT source/build trees;
- downloaded source archives created only for one verification/build;
- temporary installer build inputs;
- generated test fixture copies;
- one-off temporary virtual environments;
- temporary screenshots/video/diagnostic assets generated by automated tests.

Do not remove canonical checked-in source or the stable OWNER DEV runtime.

### 0.5 OWNER DEV retention

OWNER DEV runtime retention must be bounded.

Keep only:

- current active runtime;
- one previous-known-good rollback runtime;
- stable launcher/branding files;
- the newest useful diagnostics under the log-retention rule.

Delete older superseded OWNER DEV releases/staging directories after:

- current runtime smoke passes;
- previous-good is identified;
- no process is running from the candidate old runtime.

Log retention:

- keep at most the newest **20** startup/runtime logs;
- also remove logs older than **7 days**, except an explicitly referenced unresolved-failure log;
- never keep large binary dumps in the log directory.

### 0.6 Codex Git worktrees — safe automatic retirement

The prior machine inspection found approximately **25.4 GB** in Codex worktrees.

Do not manually delete worktree directories.

At the end of each published Codex implementation:

1. run `git worktree list --porcelain`;
2. identify worktrees created for completed PackLab tasks;
3. for each retirement candidate verify:
   - it is not the active/current M16 worktree;
   - `git status --porcelain` is empty;
   - its implementation/evidence/log commits are already reachable from `origin/main` or an explicitly preserved remote ref;
   - no unpublished commit/diff exists;
   - no running process has that worktree as its executable/current working tree where reasonably detectable;
4. remove only qualifying worktrees with `git worktree remove`;
5. run `git worktree prune`;
6. report retained dirty/active worktrees rather than deleting them.

A dirty, unpublished, active, ambiguous, or owner-created worktree must never be auto-deleted.

### 0.7 Package caches — bounded maintenance, not blind deletion

After each major local validation batch:

- run `uv cache prune`;
- record before/after uv-cache size;
- do **not** use `uv cache clean` as routine cleanup.

For pip cache:

- inspect size;
- if it exceeds **2 GiB**, use the supported pip cache command to purge/reduce it;
- never manually delete Python installations or active virtual environments.

Do not automatically delete Hugging Face, Puppeteer, Codex runtime, browser, GPU, or unrelated application caches.

### 0.8 Permanent implementation

Add a checked-in PackLab disk-hygiene helper, for example:

`tools/dev/packlab_disk_hygiene.ps1`

with modes equivalent to:

- `preflight`
- `post-test`
- `post-task`

The helper must:

- use allowlisted PackLab-generated paths only;
- print every candidate before deletion;
- support a dry-run mode;
- refuse protected roots;
- refuse ambiguous paths;
- calculate reclaimed bytes;
- fail safely on access-denied/locked files;
- never require administrator privileges.

Add a checked-in policy document describing the contract.

All future Codex PackLab prompts/runs must use this helper for local disk lifecycle management.

### 0.9 Full-test wrapper contract

Codex must stop invoking raw full local pytest directly for PackLab.

The repository-approved wrapper must:

1. run disk preflight;
2. create unique disposable basetemp;
3. invoke the locked pytest command;
4. preserve return code;
5. copy only required compact diagnostics;
6. cleanup basetemp in `finally`;
7. run post-test hygiene;
8. return the original test exit code.

Focused tiny tests may use normal pytest only if they do not create persistent temp/build trees, but the wrapper is preferred.

### 0.10 End-of-child cleanup gate

Before publishing each child Codex log:

- run post-task hygiene;
- retire safely removable completed Codex worktrees;
- prune uv cache;
- cleanup completed test basetemps/build trees;
- enforce OWNER DEV retention;
- measure C: free space again.

The child log must record:

- `disk_free_before_bytes`;
- `disk_free_after_bytes`;
- `reclaimed_bytes`;
- cleanup categories and reclaimed bytes per category;
- retained worktrees and why they were retained;
- any locked paths that could not be removed.

A child cannot report clean handoff if it leaves a known multi-GB reproducible temp tree behind without a documented active reason.

### 0.11 Acceptance floor

For this first implementation of the hygiene contract:

- inspect and safely clean stale PackLab pytest temp data;
- safely retire only provably completed/published Codex PackLab worktrees;
- prune uv cache;
- leave personal files untouched;
- leave current PackLab/OWNER DEV runtime intact;
- end with **at least 40 GiB free on C:** before resuming heavy PL-0350 V07 work.

If 40 GiB cannot be achieved using only safe PackLab-generated cleanup, stop and report exact remaining categories. Do not delete owner personal files.

Only after Phase 0 passes may PL-0350 V07 implementation/testing continue.

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

`coordination/sessions/M16-C001/MASTER_PL0350_V07_CONTINUATION_CODEX_LOG_V12.md`

If blocked, record `BATCH_STOPPED_AT_<TASK>` and end exactly:

`AWAITING_MILESTONE_AUDIT`

If PL-0350 V07 through PL-0367 all become builder-green, record:

`BATCH_COMPLETED_PRE_M17_GATE`

and end exactly:

`AWAITING_MILESTONE_AUDIT`

Final owner-facing response must use GitHub HTTPS links only.
