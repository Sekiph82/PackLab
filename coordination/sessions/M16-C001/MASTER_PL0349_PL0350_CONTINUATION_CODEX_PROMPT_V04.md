# M16-C001-R03 - PL-0349 Runtime Completeness + PL-0350 Compliance Continuation Master V04

Milestone: **M16 - CI/CD, Signing & Distribution**
Accepted frontier: **PL-0347 V02 through PL-0348**
Current child: **PL-0349 V02**
Next child: **PL-0350 V03**
Remaining after clearance: **PL-0351 through PL-0367**
Deferred gate: **PL-0368 = DEFERRED_POST_M17**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V03.md

PL-0349 V02:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0349_CODEX_PROMPT_V02.md

PL-0349 V02 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0349_CHATGPT_AUDIT_CRITERIA_V02.md

PL-0350 V03:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V03.md

PL-0350 V03 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V03.md

Master criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0349_PL0350_CONTINUATION_CHATGPT_AUDIT_CRITERIA_V04.md

Continuation log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0349_PL0350_CONTINUATION_CODEX_LOG_V04.md

## Start rule

1. Synchronize managed execution checkout non-destructively with latest `origin/main`.
2. Preserve owner-local Desktop changes and unrelated worktrees.
3. Verify live root `TASKS.md` authorizes M16-C001-R03.
4. Read partial audit V03 and both remediation child prompt/criteria packages.
5. Preserve accepted PL-0347 V02 / PL-0348 implementation and evidence.
6. Root `TASKS.md` is ChatGPT-owned. Do not edit it.
7. M17+ is unauthorized. PL-0368 remains `DEFERRED_POST_M17`.

## Phase A - PL-0349 V02

Execute PL-0349 V02 exactly.

The production frozen bundle must prove from inside the packaged executable environment:

- Qt GUI startup;
- OCP/CAD capability AVAILABLE and bounded operation PASS;
- Open3D 0.20.0 capability AVAILABLE and bounded operation PASS;
- zero hidden runtime download;
- path-free runtime capability manifest.

Do not continue to PL-0350 while either direct runtime capability is absent.

If PL-0349 V02 is builder-green:

1. publish implementation/evidence commit(s);
2. publish separate `PL-0349_CODEX_LOG_V02.md` ending `READY_FOR_INDEPENDENT_AUDIT`;
3. update original M16 master and this continuation log;
4. continue immediately to PL-0350 V03.

## Phase B - PL-0350 V03

Execute PL-0350 V03 against the exact capability-complete PL-0349 V02 staging tree.

Hard principles:

- reduce accidental shipped surface before mapping licenses;
- do not ship unused/GPL-only Qt modules under the current community route;
- do not ship Microsoft OS/MSVC runtime binaries when they are defined as external prerequisites;
- map CPython/OpenSSL correctly;
- distinguish PyInstaller build hooks from actual shipped runtime hooks;
- fully inventory actual OCP/OCCT and Open3D native surfaces;
- required LGPL/source artifacts must be exact/pinned;
- no legal-compliance certification claim;
- no installer artifact until engineering unresolved count is zero.

If PL-0350 V03 is builder-green:

1. publish implementation/evidence commit(s);
2. publish separate `PL-0350_CODEX_LOG_V03.md` ending `READY_FOR_INDEPENDENT_AUDIT`;
3. update original M16 master and this continuation log;
4. continue immediately to PL-0351.

## Phase C - Resume PL-0351 through PL-0367

Execute existing V01 prompt/criteria packages in exact order:

PL-0351 → PL-0352 → PL-0353 → PL-0354 → PL-0355 → PL-0356 → PL-0357 → PL-0358 → PL-0359 → PL-0360 → PL-0361 → PL-0362 → PL-0363 → PL-0364 → PL-0365 → PL-0366 → PL-0367.

For every green child:

- read exact prompt/criteria;
- implement only that child and accepted predecessor seams;
- run required local/static/build/security/license checks;
- obtain real hosted GitHub Actions evidence where required;
- publish implementation/evidence commit(s);
- publish distinct child-log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`;
- verify remote parity;
- update original M16 master and this continuation log;
- continue automatically while hard gates remain green.

Do not wait for intermediate ChatGPT audits.

## Retained M16 hard gates

- Windows installer artifacts remain engineering-audit artifacts until later release gates.
- PL-0351 must smoke the actually packaged/installed production application.
- PL-0352 must normalize public artifact naming/retention without weakening source/license availability obligations.
- Default iOS CI remains unsigned and secret-free.
- Optional signed IPA path remains protected/ephemeral.
- No private/proprietary scan, supplier file, production artwork, checkpoint or signing material enters public Git/artifacts.
- No Git tag/GitHub Release/V0.1 publication.
- PL-0368 remains `DEFERRED_POST_M17`.

## Stop conditions

Stop immediately on:

- missing frozen OCP/Open3D capability;
- required PackLab feature removed to simplify packaging;
- forbidden/unjustified Qt module still staged;
- unresolved shipped native file/component/license/notice/source requirement;
- inability to keep external Windows runtime prerequisite model truthful;
- unreviewed dependency/tool;
- private-data or secret leakage;
- hosted build/evidence mismatch;
- signed/unsigned provenance ambiguity;
- release/version ambiguity;
- need to start PL-0368 or M17;
- owner-required decision.

On stop:

- preserve completed green remediation/children;
- publish exact blocker evidence;
- record `BATCH_STOPPED`;
- keep PL-0368 deferred;
- end continuation log exactly `AWAITING_MILESTONE_AUDIT`;
- stop.

## Successful pre-M17 handoff

If PL-0349 V02, PL-0350 V03 and PL-0351→PL-0367 are builder-green:

- all executable M16 work has distinct implementation/evidence + child logs;
- frozen Windows production app is capability-complete;
- PL-0350 engineering redistribution inventory is exact-artifact green;
- required license/source evidence accompanies audit artifacts;
- Windows/iOS build/signing/provenance/release-engineering children are builder-green;
- no Git tag/GitHub Release exists;
- PL-0368 remains `DEFERRED_POST_M17`;
- final local/origin/GitHub parity is clean;
- M17 started: NO;
- record `BATCH_COMPLETED_PRE_M17_GATE`;
- end exactly `AWAITING_MILESTONE_AUDIT`;
- stop for independent ChatGPT audit.
