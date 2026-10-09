# M16-C001-R08 - PL-0350 V07 Controlled Runtime Cache + PL-0351 Clean Install + PL-0352→PL-0367 Continuation Master V12

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
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0350_V07_CONTINUATION_CHATGPT_AUDIT_CRITERIA_V12.md

Required master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0350_V07_CONTINUATION_CODEX_LOG_V12.md

## Start rule

1. Synchronize the managed Codex checkout non-destructively with latest `origin/main`.
2. Preserve owner-local work and unrelated worktrees.
3. Read live root `TASKS.md`; it must authorize M16-C001-R08 / PL-0350 V07.
4. Read partial audit V09, V06 audit, V07 prompt and criteria.
5. Preserve the working native Desktop `PackLab.exe`.
6. Do not edit root `TASKS.md`.
7. Do not start M17 or PL-0368.

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
