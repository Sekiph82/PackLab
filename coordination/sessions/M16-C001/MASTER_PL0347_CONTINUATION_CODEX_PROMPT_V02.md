# M16-C001-R01 - PL-0347 Mypy Remediation & Continuation Master V02

Milestone: **M16 - CI/CD, Signing & Distribution**
Current child: **PL-0347 V02**
Remaining after closure: **PL-0348 through PL-0367**
Deferred gate: **PL-0368 = DEFERRED_POST_M17**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V01.md

PL-0347 V02:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0347_CODEX_PROMPT_V02.md

PL-0347 V02 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0347_CHATGPT_AUDIT_CRITERIA_V02.md

Continuation criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0347_CONTINUATION_CHATGPT_AUDIT_CRITERIA_V02.md

Continuation log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL0347_CONTINUATION_CODEX_LOG_V02.md

## Start rule

1. Synchronize the managed execution checkout non-destructively with latest `origin/main`.
2. Preserve owner-local Desktop changes and unrelated worktrees.
3. Verify live root `TASKS.md` authorizes M16-C001-R01.
4. Read the partial audit and PL-0347 V02 prompt/criteria.
5. Preserve PL-0347 V01 workflow behavior except where V02 explicitly authorizes source remediation.
6. Root `TASKS.md` is ChatGPT-owned. Do not edit it.
7. M17+ is unauthorized. PL-0368 remains `DEFERRED_POST_M17`.

## Phase A - PL-0347 V02

Execute PL-0347 V02 exactly.

The hard quality gate remains:

`uv run --locked mypy core apps tools`

No baseline, exclude, ignore, soft-fail or scope reduction.

PL-0347 V02 must produce a fresh hosted Windows Actions run in which every required quality step passes.

If V02 is builder-green:

1. publish implementation/evidence commit(s);
2. publish separate `PL-0347_CODEX_LOG_V02.md` ending `READY_FOR_INDEPENDENT_AUDIT`;
3. update the original M16 master log and this continuation log;
4. continue immediately to PL-0348.

## Phase B - Resume PL-0348 through PL-0367

Execute the existing V01 prompt/criteria packages in exact order:

PL-0348 → PL-0349 → PL-0350 → PL-0351 → PL-0352 → PL-0353 → PL-0354 → PL-0355 → PL-0356 → PL-0357 → PL-0358 → PL-0359 → PL-0360 → PL-0361 → PL-0362 → PL-0363 → PL-0364 → PL-0365 → PL-0366 → PL-0367.

For every green child:

- read its exact prompt/criteria;
- implement only that child and accepted predecessor seams;
- run required local/static/build/security/license checks;
- obtain real hosted GitHub Actions evidence where the child requires it;
- publish implementation/evidence commit(s);
- publish a distinct child-log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`;
- verify remote parity;
- update original master and continuation logs;
- continue automatically while all hard gates remain green.

Do not wait for intermediate ChatGPT audit.

## Retained hard gates

- PL-0350 Windows redistribution/license inventory remains a HARD STOP if actual shipped native/runtime files cannot be truthfully inventoried and packaged with required notices.
- Default iOS CI remains unsigned and secret-free.
- Optional signed IPA path must remain protected and secret-safe.
- No private/proprietary scan, supplier file, production artwork or signing material enters public Git/artifacts.
- No tag/GitHub Release is created.
- PL-0368 is not executed before M17.

## Stop conditions

Stop immediately on:

- mypy still nonzero after honest remediation;
- runtime/authority regression caused by type cleanup;
- unresolved Windows redistribution/license inventory;
- unreviewed dependency;
- secret/private-data leakage risk;
- hosted CI/build evidence failure where mandatory;
- signed/unsigned provenance ambiguity;
- release/version ambiguity;
- need to start M17 or PL-0368;
- owner-required decision.

On stop:

- preserve completed green children;
- publish exact blocker evidence;
- record `BATCH_STOPPED`;
- keep PL-0368 deferred;
- end continuation log exactly `AWAITING_MILESTONE_AUDIT`;
- stop.

## Successful pre-M17 handoff

If PL-0347 V02 and PL-0348 through PL-0367 are builder-green:

- all executable M16 children have implementation/evidence + distinct child logs;
- hosted Windows quality is genuinely green with mypy zero;
- redistribution gate is truthfully closed;
- Windows/iOS build/signing/provenance/release-engineering children are builder-green;
- no Git tag/GitHub Release exists;
- PL-0368 remains `DEFERRED_POST_M17`;
- final local/origin/GitHub parity is clean;
- M17 started: NO;
- record `BATCH_COMPLETED_PRE_M17_GATE`;
- end exactly `AWAITING_MILESTONE_AUDIT`;
- stop for independent ChatGPT audit.
