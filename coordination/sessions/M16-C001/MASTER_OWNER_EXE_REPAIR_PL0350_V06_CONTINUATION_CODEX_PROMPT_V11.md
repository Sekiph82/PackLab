# M16-C001-R07 - OWNER DESKTOP EXE STARTUP REPAIR + PL-0350 V06 Controlled Native Provenance + PL-0351 Clean Install + PL-0352→PL-0367 Continuation Master V11

Milestone: **M16 - CI/CD, Signing & Distribution**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Accepted frontier:

- PL-0347 V02: AUDITED_PASS
- PL-0348: AUDITED_PASS
- PL-0349 V03: AUDITED_PASS
- Owner Desktop native PackLab.exe: AUDITED_PASS

Current child:

- **PL-0350 V06 — provenance-complete controlled Windows native runtime + unsigned installer closure**

Then, only if green:

- **PL-0351 V01 — clean-installed PackLabStudio portability / QtCore loader smoke**
- **PL-0352 through PL-0367 — existing ordered M16 continuation**
- **PL-0368 remains DEFERRED_POST_M17**

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V08.md

PL-0350 V06 prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V06.md

PL-0350 V06 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V06.md

PL-0351 prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CODEX_PROMPT_V01.md

PL-0351 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CHATGPT_AUDIT_CRITERIA_V01.md

Master criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0350_V06_CONTINUATION_CHATGPT_AUDIT_CRITERIA_V10.md

Required master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0350_V06_CONTINUATION_CODEX_LOG_V10.md

## Start rule

1. Synchronize the managed Codex checkout non-destructively with latest `origin/main`.
2. Preserve owner-local work and unrelated worktrees.
3. Read live root `TASKS.md`; it must authorize M16-C001-R07 / PL-0350 V06.
4. Read partial audit V08, V05 audit, V06 child prompt and criteria.
5. Treat the native Desktop `PackLab.exe` implementation as structurally accepted but current runtime health as FAILED by fresh owner evidence; execute Phase 0 before PL-0350 V06.
6. Do not edit root `TASKS.md`.
7. Do not start M17 or PL-0368.

## Phase 0 - OWNER DESKTOP PackLab.exe startup repair — MUST PASS FIRST

This is part of the current R07 master. Do **not** create a separate task, milestone, tracker or continuation.

The owner has now provided real-machine evidence that the current Desktop `PackLab.exe` does **not** launch PackLab successfully.

Observed owner result:

- double-clicking the actual Desktop `PackLab.exe` shows a native error dialog:
  `PackLab Studio could not start. Details: %LOCALAPPDATA%\\PackLab\\OwnerDev\\logs\\startup-<timestamp>.log`
- therefore the earlier owner-local native EXE acceptance is superseded for current runtime health;
- PL-0350 V06 work must **not** start until this real owner launch failure is reproduced, diagnosed and fixed.

### 0.1 Read the actual owner-local failure first

Before changing source:

1. identify the newest `%LOCALAPPDATA%\PackLab\OwnerDev\logs\startup-*.log` corresponding to the owner's failed Desktop launch;
2. read it in full;
3. capture:
   - deployed source SHA;
   - Studio version;
   - launcher failure category;
   - child exit code if present;
   - Python exception type/message/traceback if present;
   - missing path/module/DLL/runtime detail if present;
4. correlate that log to the current Desktop `PackLab.exe` and current `owner-dev-runtime.json`;
5. record the exact root cause in the R07 master log.

Do not guess the cause from prior runs.

### 0.2 Reproduce from the actual Desktop EXE

Use the real Windows Desktop known-folder `PackLab.exe`.

Do not launch:

- Python directly;
- the repository module directly;
- a worktree-local launcher;
- the old Desktop LNK;
- a temporary test EXE.

Reproduce the failure from the same user-facing entry point the owner double-clicks.

### 0.3 Fix the actual root cause

Fix whatever the real startup log proves is broken.

Possible areas include, but are not limited to:

- stale OWNER DEV runtime after Git publication;
- runtime manifest SHA mismatch;
- bootstrap/runtime path mismatch;
- missing copied runtime file;
- stale `.venv`;
- missing/incorrect dependency sync;
- Python import path failure;
- Qt/PySide DLL resolution;
- launcher environment inheritance;
- current/launcher atomic swap race;
- source/runtime version skew;
- post-Codex refresh not actually updating the owner's real LocalAppData runtime.

Do not paper over the error by increasing timeouts or suppressing the error dialog.

### 0.4 Make the runtime self-consistent

The post-Codex refresh must guarantee that these four identities all match the same published Git HEAD:

- `owner-dev-runtime.json.source_commit`;
- runtime source tree copied under `OwnerDev\current`;
- runtime `.venv` dependency environment;
- Desktop/native launcher handoff.

Add explicit consistency validation if missing.

If runtime dependencies can become stale across source changes, fix the refresh so `uv sync --locked --no-install-project` truthfully updates the active runtime before it is promoted.

### 0.5 Real owner-machine acceptance gate

After publishing the fix and refreshing from exact published `origin/main`:

1. close only PackLab processes created by Codex's own previous failed/repro test;
2. verify there is no unrelated existing PackLab Studio window that could create a false positive;
3. Shell-open the actual Desktop `PackLab.exe`;
4. correlate:
   - Desktop launcher PID;
   - child `pythonw.exe` process chain;
   - actual visible PackLab Studio process/window;
5. verify title exactly `PackLab Studio`;
6. verify the app remains alive and the window remains visible for **at least 60 continuous seconds**;
7. during that 60-second interval, interact minimally enough to prove the Qt event loop remains responsive, for example focus/activate the window and process a benign UI event without changing owner data;
8. verify no new startup error log was created for the successful launch;
9. verify no PowerShell/console window remains;
10. verify the Desktop EXE embedded icon remains valid;
11. verify deployed runtime SHA equals current published GitHub `main`;
12. **leave exactly one working PackLab Studio window open for the owner after handoff**.

If the application closes or errors during this 60-second gate:

- read the new startup log;
- fix the actual cause;
- rerun the gate;
- do not proceed to PL-0350 V06.

### 0.6 Prevent false PASS evidence

The R07 log must not claim OWNER DEV success merely because:

- a source-mode smoke passed;
- a temporary Python process stayed alive;
- a window from an earlier process existed;
- a 10/30-second launcher monitor passed while the real Desktop app later failed;
- the native launcher itself returned zero.

Success means the owner's **actual Desktop PackLab.exe** opens the current PackLab Studio and remains healthy for the full 60-second acceptance.

### 0.7 Publication and GitHub-link evidence

Publish the owner startup repair implementation/evidence before continuing.

In the R07 master log include GitHub HTTPS links for:

- implementation commit(s);
- any checked-in evidence document;
- relevant prompt/criteria;
- current GitHub `main` commit.

Do not use local `C:\...\` paths as owner-facing links.

The owner-local startup log itself must remain local/private and must not be committed if it contains machine-specific paths or diagnostics. Summarize only safe findings in the GitHub log.

Only after Phase 0 passes may you begin PL-0350 V06.

## Phase A - PL-0350 V06

Execute PL-0350 V06 exactly.

Core strategy change:

- stop reverse-guessing opaque OCP wheel provenance;
- produce a PackLab-controlled provenance-complete OCP/OCCT Windows runtime from exact locked source/package inputs;
- close the remaining Qt/PySide/Shiboken and Open3D official source/notice evidence;
- preserve real frozen capability.

If blocked:

- publish implementation/evidence;
- publish exact hosted blocker evidence;
- publish `PL-0350_CODEX_LOG_V06.md`;
- verify local/origin/GitHub parity;
- refresh OWNER DEV native Desktop EXE;
- publish/update the master log;
- stop;
- do not start PL-0351.

If green, PL-0350 must have:

- zero unresolved shipped files/components;
- zero missing notices/source packages;
- zero forbidden Qt components;
- fresh frozen Qt GUI/QtPdf/OCP/Open3D smoke PASS;
- exact controlled native source lock/provenance evidence;
- cleared versioned unsigned installer artifact.

Then continue immediately to PL-0351.

## Phase B - PL-0351 clean installed-artifact portability

Execute the existing amended PL-0351 V01 prompt/criteria.

Mandatory architecture:

- separate fresh Windows job;
- download exact cleared PL-0350 installer;
- verify artifact hash and byte length;
- install silently into isolated path;
- sanitize repo/venv/Python/Qt/Shiboken/OCP/Open3D/developer paths;
- launch the installed `PackLabStudio.exe`;
- require real Qt GUI + QtPdf + OCP/CAD + Open3D smoke;
- hard-fail DLL load/procedure/entry-point/ICU/plugin/Shiboken/architecture errors;
- cleanup/uninstall even on failure.

This is the permanent installed-artifact regression gate for the prior owner-observed QtCore missing-procedure failure.

If PL-0351 fails, publish exact GitHub-hosted evidence and stop. Do not start PL-0352.

If green, publish child implementation/evidence + distinct child log and continue.

## Phase C - PL-0352 through PL-0367

Execute existing child prompt/criteria packages in exact order:

PL-0352 → PL-0353 → PL-0354 → PL-0355 → PL-0356 → PL-0357 → PL-0358 → PL-0359 → PL-0360 → PL-0361 → PL-0362 → PL-0363 → PL-0364 → PL-0365 → PL-0366 → PL-0367.

For each completed child:

- implement only authorized scope;
- run required local/hosted validation;
- publish implementation/evidence;
- publish distinct child Codex log;
- verify local/origin/GitHub parity;
- refresh OWNER DEV native Desktop EXE;
- continue automatically while all gates remain green.

Do not wait for intermediate ChatGPT audit.

## GitHub-link handoff contract

Every Codex handoff to the owner must use GitHub HTTPS links.

For each child/master handoff provide clickable links for all applicable:

- task prompt;
- audit criteria;
- implementation commit(s);
- evidence commit(s);
- child Codex log;
- master Codex log;
- GitHub Actions quality run;
- GitHub Actions build/test run;
- GitHub Actions artifacts.

Do not present local `C:\...` paths as owner handoff links.

Published child/master logs must also use GitHub URLs for referenced repository files, commits, Actions runs and artifacts where useful.

## OWNER DEV native Desktop EXE standing rule

After each published implementation/evidence commit and verified remote parity:

- run the native OWNER DEV refresh;
- verify Desktop `PackLab.exe`;
- do not recreate the obsolete Desktop `PackLab.lnk`;
- do not regress to PowerShell launch;
- record `OWNER_DEV_EXE_READY` in the log.

## Retained gates

- no private scans/supplier data/credentials/signing material in public repo/artifacts;
- default iOS path stays unsigned/secret-free;
- no tag/GitHub Release/V0.1 before PL-0368;
- PL-0368 remains `DEFERRED_POST_M17`;
- M17 must not start.

## Stop conditions

Stop on any real:

- unresolved provenance/source/license/notice item;
- controlled native build non-reproducibility;
- source/package hash mismatch;
- frozen capability regression;
- installed-artifact loader failure;
- artifact provenance mismatch;
- privacy/secret leak;
- signing/release ambiguity;
- owner-required decision;
- need to start PL-0368/M17.

## Handoff

Required master log:

`coordination/sessions/M16-C001/MASTER_PL0350_V06_CONTINUATION_CODEX_LOG_V10.md`

If blocked, record `BATCH_STOPPED_AT_<TASK>` and end exactly:

`AWAITING_MILESTONE_AUDIT`

If PL-0350 V06 through PL-0367 all become builder-green, record:

`BATCH_COMPLETED_PRE_M17_GATE`

and end exactly:

`AWAITING_MILESTONE_AUDIT`

The final owner-facing response must use only GitHub HTTPS links for logs/evidence/commits/runs/artifacts.
