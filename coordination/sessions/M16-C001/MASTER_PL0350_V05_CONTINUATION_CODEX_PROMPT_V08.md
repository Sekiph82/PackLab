# M16-C001-R06 - OWNER DEV Launcher Repair + PL-0350 V05 Final Native Evidence + PL-0351 Clean Install + PL-0352→PL-0367 Continuation Master V08

Milestone: **M16 - CI/CD, Signing & Distribution**
Accepted frontier: **PL-0347 V02 through PL-0349 V03**
OWNER DEV launcher: **INTEGRATED REPAIR REQUIRED before PL-0350 V05**
Current child: **PL-0350 V05**
Next child: **PL-0351 amended clean-artifact portability smoke**
Remaining after clearance: **PL-0352 through PL-0367**
Deferred gate: **PL-0368 = DEFERRED_POST_M17**

Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V07.md

PL-0350 V05:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V05.md

PL-0350 V05 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V05.md

PL-0351 amended prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CODEX_PROMPT_V01.md

PL-0351 amended criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CHATGPT_AUDIT_CRITERIA_V01.md

Master criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0350_V05_CONTINUATION_CHATGPT_AUDIT_CRITERIA_V08.md

Continuation log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0350_V05_CONTINUATION_CODEX_LOG_V08.md

## Start rule

1. Synchronize managed Codex checkout non-destructively with latest `origin/main`.
2. Preserve owner-local Desktop work and unrelated worktrees.
3. Read live root `TASKS.md`; it must authorize M16-C001-R06 / PL-0350 V05.
4. Read partial audit V07, PL-0350 V04 audit, PL-0350 V05 prompt/criteria.
5. Preserve accepted PL-0347 V02 through PL-0349 V03 and OWNER DEV behavior.
6. Do not edit root `TASKS.md`.
7. Do not start M17 or PL-0368.

## Phase 0 - Integrated OWNER DEV launcher repair

This is part of the current R06 master. Do **not** open a separate OWNER DEV task, tracker, milestone or continuation.

Before touching PL-0350 redistribution work, execute the integrated OWNER DEV repair requirements now embedded in the live `PL-0350_CODEX_PROMPT_V05.md` and criteria.

The owner has real desktop evidence of two defects:

1. Desktop `PackLab.lnk` shows a generic white-document icon instead of the canonical PackLab icon.
2. Double-click starts PackLab briefly and it closes almost immediately.

Mandatory repair:

- move shortcut icon authority to stable `%LOCALAPPDATA%\PackLab\OwnerDev\branding\PackLab.ico`;
- keep canonical SHA-256 `a4a655fc92796413130633703602885671f5b1a0773d045ebc79d6bd522c7fc1`;
- Desktop + Start Menu shortcuts must use that stable ICO path, never `OwnerDev\current`;
- recreate shortcuts deterministically and perform a non-destructive Shell refresh/notification;
- launcher must use `Start-Process -PassThru` and monitor the child for at least 8 seconds;
- any early `pythonw` exit must produce a real local diagnostic with exit code and startup exception details, not a silent/generic success;
- add OWNER-DEV-only traceback logging without weakening production exception handling;
- run the actual Desktop `PackLab.lnk` through Windows Shell `open`;
- the PackLab Studio window must remain alive and visible for at least 15 continuous seconds;
- verify nonzero window icon handle and stable shortcut icon path/hash;
- close the window deliberately only after the 15-second proof;
- emit `OWNER_DEV_READY` only after all runtime/shortcut/icon checks pass.

If the Desktop launch closes before 15 seconds, inspect the generated local log and fix the actual cause. **Do not proceed to PL-0350 V05 while the owner launcher is still broken.**

Publish the repair as part of the current R06 implementation sequence and record its commit(s) in the R06 master log. No separate child/task log is required unless the existing repository logging contract forces one.

## Phase A - PL-0350 V05

Execute PL-0350 V05 exactly.

The only permitted unresolved frontier is the five native component gates:

- cadquery-ocp-novtk;
- open3d;
- pyside6-addons;
- pyside6-essentials;
- shiboken6;

plus their aggregate missing-source-evidence gate.

V05 must use machine-readable exact file maps and verified corresponding source evidence. It must not clear component status through blanket registry edits.

If PL-0350 V05 remains blocked:

- publish implementation/evidence;
- publish exact updated text-only pre-clearance evidence;
- publish distinct `PL-0350_CODEX_LOG_V05.md`;
- verify remote parity;
- run OWNER DEV post-Codex refresh;
- record `BATCH_STOPPED_AT_PL-0350_V05`;
- end the continuation log exactly `AWAITING_MILESTONE_AUDIT`;
- stop.

Do not start PL-0351.

If PL-0350 V05 is builder-green, it must include:

- zero unresolved shipped files/components;
- zero missing notices/source packages;
- zero forbidden Qt components;
- fresh frozen Qt/PDF/OCP/Open3D smoke PASS;
- verified required source evidence;
- versioned unsigned installer artifact;
- final compliance/source audit artifacts.

Then continue immediately to PL-0351.

## Phase B - PL-0351 clean-artifact portability smoke

Execute the current amended PL-0351 V01 prompt/criteria.

Mandatory:

- separate fresh Windows job;
- download the exact PL-0350 cleared installer artifact;
- verify installer hash/length;
- install into isolated path;
- sanitize source/venv/Qt/Shiboken/OCP/Open3D/developer paths;
- launch the installed PackLabStudio.exe;
- require real Qt GUI + QtPdf + OCP/CAD + Open3D smoke;
- hard fail on DLL load, procedure, entry-point, ICU, plugin, Shiboken or architecture mismatch;
- uninstall/cleanup even on failure.

This is the permanent regression gate for the owner's repeated local QtCore error.

If PL-0351 fails, stop truthfully and do not start PL-0352.

If PL-0351 is builder-green:

- publish implementation/evidence;
- publish distinct child log ending `READY_FOR_INDEPENDENT_AUDIT`;
- verify parity;
- run OWNER DEV refresh;
- continue to PL-0352.

## Phase C - PL-0352 through PL-0367

Execute existing V01 prompt/criteria packages in exact order:

PL-0352 → PL-0353 → PL-0354 → PL-0355 → PL-0356 → PL-0357 → PL-0358 → PL-0359 → PL-0360 → PL-0361 → PL-0362 → PL-0363 → PL-0364 → PL-0365 → PL-0366 → PL-0367.

For each green child:

- read exact prompt/criteria;
- implement only that child and accepted predecessor seams;
- run required local/hosted validation;
- publish implementation/evidence;
- publish distinct child log ending `READY_FOR_INDEPENDENT_AUDIT`;
- verify local/origin/GitHub parity;
- run `tools/dev/post_codex_owner_dev_refresh.ps1 -AllowPublishedCommit`;
- record the OWNER DEV result;
- continue automatically while all hard gates remain green.

Do not wait for intermediate ChatGPT audit.

## Retained hard gates

- OWNER DEV source launcher is for manual owner testing and does not substitute for installer portability.
- No private scans, supplier files, project data, credentials, checkpoints or signing material in public Git/artifacts.
- Default iOS CI remains unsigned and secret-free.
- Optional signed IPA stays protected/ephemeral.
- No Git tag, GitHub Release or V0.1 publication before PL-0368.
- PL-0368 remains `DEFERRED_POST_M17`.
- M17 must not start.

## Stop conditions

Stop immediately on:

- any unresolved native component/source/notice item;
- source hash mismatch;
- packaged Qt/PDF/OCP/Open3D regression;
- installed-artifact loader failure;
- artifact provenance mismatch;
- unauthorized runtime download;
- secret/private-data leakage;
- signing/provenance ambiguity;
- release/version ambiguity;
- owner-required decision;
- need to start PL-0368 or M17.

On stop:

- preserve completed green work;
- publish exact blocker evidence;
- update master log;
- end exactly `AWAITING_MILESTONE_AUDIT`.

## Successful pre-M17 handoff

If PL-0350 V05 and PL-0351 through PL-0367 are builder-green:

- final Windows engineering redistribution gate is green;
- clean installed-artifact portability smoke is green;
- all executable M16 pre-M17 children are builder-green;
- OWNER DEV reflects final published HEAD;
- no tag/GitHub Release exists;
- PL-0368 remains `DEFERRED_POST_M17`;
- M17 started: NO;
- local/origin/GitHub parity clean;
- record `BATCH_COMPLETED_PRE_M17_GATE`;
- end exactly `AWAITING_MILESTONE_AUDIT`.
