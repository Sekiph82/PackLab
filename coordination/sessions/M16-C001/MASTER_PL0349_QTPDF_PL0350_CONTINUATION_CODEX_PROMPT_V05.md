# M16-C001-R04 - PL-0349 QtPdf Runtime Completeness + PL-0350 Compliance Continuation Master V05

Milestone: **M16 - CI/CD, Signing & Distribution**
Accepted frontier: **PL-0347 V02 through PL-0348**
Current child: **PL-0349 V03**
Next child: **PL-0350 V03**
Remaining after clearance: **PL-0351 through PL-0367**
Deferred gate: **PL-0368 = DEFERRED_POST_M17**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V04.md

PL-0349 V03:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0349_CODEX_PROMPT_V03.md

PL-0349 V03 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0349_CHATGPT_AUDIT_CRITERIA_V03.md

PL-0350 V03:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V03.md

PL-0350 V03 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V03.md

Master criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0349_QTPDF_PL0350_CONTINUATION_CHATGPT_AUDIT_CRITERIA_V05.md

Continuation log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0349_QTPDF_PL0350_CONTINUATION_CODEX_LOG_V05.md

## Start rule

1. Synchronize managed execution checkout non-destructively with latest `origin/main`.
2. Preserve owner-local Desktop changes and unrelated worktrees.
3. Verify live root `TASKS.md` authorizes M16-C001-R04.
4. Read partial audit V04 plus PL-0349 V03 and PL-0350 V03 packages.
5. Preserve accepted PL-0347 V02 / PL-0348 implementation and evidence.
6. Root `TASKS.md` is ChatGPT-owned. Do not edit it.
7. M17+ is unauthorized. PL-0368 remains `DEFERRED_POST_M17`.

## Phase A - PL-0349 V03

Execute PL-0349 V03 exactly.

Key corrected rule:

- PySide6 Addons is not categorically forbidden.
- PackLab requires `QtPdf` for technical-drawing PDF.
- Preserve that capability.
- Freeze only the exact required Addons/Qt surface.
- Do not stage Virtual Keyboard or other unapproved/GPL-only module families.
- Frozen executable must prove Qt GUI + Qt PDF + OCP/CAD + Open3D capability.

If PL-0349 V03 is builder-green:

1. publish implementation/evidence commit(s);
2. publish separate `PL-0349_CODEX_LOG_V03.md` ending `READY_FOR_INDEPENDENT_AUDIT`;
3. update original M16 master and this continuation log;
4. continue immediately to PL-0350 V03.

## Phase B - PL-0350 V03

Execute PL-0350 V03 against the exact PL-0349 V03 capability-complete stage.

Hard principles:

- inventory actual shipped files only;
- map retained QtPdf/Essentials/Addons modules at module/file level;
- include exact Qt PDF third-party notices;
- provide exact required LGPL/source evidence;
- no forbidden/unjustified Qt modules;
- keep Microsoft system runtime as explicit external prerequisite where the frozen smoke remains valid after pruning;
- map CPython/OpenSSL correctly;
- distinguish PyInstaller build hooks from shipped runtime hooks;
- fully map OCP/OCCT and Open3D native surface;
- engineering packaging clearance is not legal/public-release authorization.

If PL-0350 V03 is builder-green:

1. publish implementation/evidence commit(s);
2. publish separate `PL-0350_CODEX_LOG_V03.md` ending `READY_FOR_INDEPENDENT_AUDIT`;
3. update original M16 master and this continuation log;
4. continue immediately to PL-0351.

## Phase C - Resume PL-0351 through PL-0367

Execute existing V01 prompt/criteria packages in exact order:

PL-0351 → PL-0352 → PL-0353 → PL-0354 → PL-0355 → PL-0356 → PL-0357 → PL-0358 → PL-0359 → PL-0360 → PL-0361 → PL-0362 → PL-0363 → PL-0364 → PL-0365 → PL-0366 → PL-0367.

For each green child:

- read exact prompt/criteria;
- implement only that child and accepted predecessor seams;
- run required local/static/build/security/license checks;
- obtain real hosted GitHub Actions evidence where required;
- publish implementation/evidence commit(s);
- publish distinct child-log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`;
- verify remote parity;
- update original M16 master and this continuation log;
- continue automatically while hard gates remain green.

Do not wait for intermediate ChatGPT audit.

## Stop conditions

Stop immediately on:

- accepted PDF capability removed or stubbed;
- frozen QtPdf/OCP/Open3D capability failure;
- forbidden/unjustified Qt module staged;
- unresolved shipped file/component/license/notice/source requirement;
- required feature removed merely to simplify licensing;
- unreviewed dependency/tool;
- private-data or secret leakage;
- hosted build/evidence mismatch;
- signed/unsigned provenance ambiguity;
- release/version ambiguity;
- need to start PL-0368 or M17;
- owner-required decision.

On stop:

- preserve completed green work;
- publish exact blocker evidence;
- record `BATCH_STOPPED`;
- keep PL-0368 deferred;
- end continuation log exactly `AWAITING_MILESTONE_AUDIT`;
- stop.

## Successful pre-M17 handoff

If PL-0349 V03, PL-0350 V03 and PL-0351→PL-0367 are builder-green:

- frozen Windows app is capability-complete, including real Qt PDF;
- Windows engineering redistribution evidence is exact-artifact green;
- required license/source evidence accompanies audit artifacts;
- Windows/iOS build/signing/provenance/release-engineering children are builder-green;
- no Git tag/GitHub Release exists;
- PL-0368 remains `DEFERRED_POST_M17`;
- final local/origin/GitHub parity is clean;
- M17 started: NO;
- record `BATCH_COMPLETED_PRE_M17_GATE`;
- end exactly `AWAITING_MILESTONE_AUDIT`;
- stop for independent ChatGPT audit.
