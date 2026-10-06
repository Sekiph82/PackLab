# M16-C001-R05 - PL-0350 V04 Redistribution Closure + PL-0351 Clean Install + PL-0352→PL-0367 Continuation Master V06

Milestone: **M16 - CI/CD, Signing & Distribution**
Accepted frontier: **PL-0347 V02 through PL-0349 V03**
Owner-local launcher: **AUDITED_PASS**
Current child: **PL-0350 V04**
Next child: **PL-0351 amended clean-artifact portability smoke**
Remaining after clearance: **PL-0352 through PL-0367**
Deferred gate: **PL-0368 = DEFERRED_POST_M17**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V06.md

PL-0350 V04:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V04.md

PL-0350 V04 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V04.md

PL-0351 amended prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CODEX_PROMPT_V01.md

PL-0351 amended criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CHATGPT_AUDIT_CRITERIA_V01.md

Master criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0350_V04_CONTINUATION_CHATGPT_AUDIT_CRITERIA_V06.md

Continuation log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0350_V04_CONTINUATION_CODEX_LOG_V06.md

## Start rule

1. Synchronize the managed Codex checkout non-destructively with latest `origin/main`.
2. Preserve owner-local Desktop work and unrelated worktrees.
3. Read live root `TASKS.md`; it must authorize M16-C001-R05 / PL-0350 V04.
4. Read partial audit V06, PL-0350 V03 audit and V04 prompt/criteria.
5. Preserve accepted PL-0347 V02 through PL-0349 V03.
6. Preserve OWNER DEV launcher behavior and standing refresh policy.
7. Do not edit root `TASKS.md`.
8. Do not start M17 or PL-0368.

## Phase A - PL-0350 V04

Execute PL-0350 V04 exactly.

The frozen baseline is the exact V03 59-item engineering gate. Close the actual remaining shipped-file/component/source/notice surface, not a generic dependency list.

If V04 remains blocked:

- publish exact updated text-only evidence;
- publish implementation/evidence + distinct `PL-0350_CODEX_LOG_V04.md`;
- run OWNER DEV post-Codex refresh after remote parity;
- record `BATCH_STOPPED_AT_PL-0350_V04`;
- end master log `AWAITING_MILESTONE_AUDIT`;
- stop.

Do not start PL-0351.

If V04 is builder-green, it must have:

- zero unresolved shipped files/components;
- zero missing required notices/source evidence;
- post-prune Qt/PDF/OCP/Open3D frozen smoke PASS;
- versioned unsigned installer artifact;
- final compliance/source artifacts.

Then continue automatically to PL-0351.

## Phase B - PL-0351 amended clean-artifact portability smoke

Execute the current amended PL-0351 V01 prompt/criteria, not the historical shorter interpretation.

Mandatory architecture:

- separate fresh Windows job;
- download exact cleared PL-0350 installer artifact;
- verify hash/length;
- silently install into isolated path;
- sanitize PATH/Python/Qt/Shiboken/OCP/Open3D/developer environment;
- launch the **installed** PackLabStudio.exe;
- require real Qt GUI + QtPdf + OCP + Open3D capability smoke;
- hard fail on DLL load/procedure/entry-point/ICU/Shiboken/plugin errors;
- cleanup/uninstall even on failure.

This is the permanent regression gate for the owner-observed local `QtCore: The specified procedure could not be found` failure.

If PL-0351 fails, stop and publish exact loader/install evidence. Do not start PL-0352.

If PL-0351 is builder-green, publish implementation/evidence + distinct child log ending `READY_FOR_INDEPENDENT_AUDIT`, run OWNER DEV refresh, then continue.

## Phase C - PL-0352 through PL-0367

Execute the existing V01 prompt/criteria packages in exact order:

PL-0352 → PL-0353 → PL-0354 → PL-0355 → PL-0356 → PL-0357 → PL-0358 → PL-0359 → PL-0360 → PL-0361 → PL-0362 → PL-0363 → PL-0364 → PL-0365 → PL-0366 → PL-0367.

For every green child:

- read exact child prompt/criteria;
- implement only that child and accepted predecessor seams;
- obtain real hosted evidence where required;
- publish implementation/evidence;
- publish distinct child log ending `READY_FOR_INDEPENDENT_AUDIT`;
- verify local/origin/GitHub parity;
- run `tools/dev/post_codex_owner_dev_refresh.ps1 -AllowPublishedCommit`;
- record `OWNER_DEV_READY` or truthful owner-local delivery failure;
- continue automatically while all hard gates remain green.

Do not wait for intermediate ChatGPT audit.

## Retained hard gates

- OWNER DEV source launcher is for owner manual testing and never substitutes for installer portability evidence.
- No private/proprietary scans, supplier files, project state, checkpoints, credentials or signing material in public Git/artifacts.
- Default iOS CI remains unsigned/secret-free.
- Optional signed IPA remains protected/ephemeral.
- No Git tag/GitHub Release/V0.1 publication before PL-0368.
- PL-0368 remains `DEFERRED_POST_M17`.
- M17 must not start.

## Stop conditions

Stop on:

- any unresolved redistribution/source/notice item;
- Qt/PDF/OCP/Open3D packaged capability regression;
- clean installed-artifact loader failure;
- artifact provenance mismatch;
- unauthorized runtime download;
- secret/private-data leak;
- signed/unsigned ambiguity;
- release/version ambiguity;
- owner-required decision;
- need to start PL-0368 or M17.

On stop:

- preserve completed green work;
- publish exact blocker evidence;
- update master log;
- end exactly `AWAITING_MILESTONE_AUDIT`.

## Successful pre-M17 handoff

If PL-0350 V04 and PL-0351 through PL-0367 are builder-green:

- Windows installer engineering gate is exact-artifact green;
- separate clean-install portability smoke is green;
- all executable M16 pre-M17 children are builder-green;
- OWNER DEV runtime/shortcuts reflect final published HEAD;
- no tag/GitHub Release exists;
- PL-0368 remains `DEFERRED_POST_M17`;
- M17 started: NO;
- local/origin/GitHub parity clean;
- record `BATCH_COMPLETED_PRE_M17_GATE`;
- end exactly `AWAITING_MILESTONE_AUDIT`.
