# M16-C001-R07 - PL-0350 V06 Controlled Native Provenance + PL-0351 Clean Install + PL-0352→PL-0367 Continuation Master V10

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
5. Preserve the accepted native Desktop `PackLab.exe`.
6. Do not edit root `TASKS.md`.
7. Do not start M17 or PL-0368.

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
