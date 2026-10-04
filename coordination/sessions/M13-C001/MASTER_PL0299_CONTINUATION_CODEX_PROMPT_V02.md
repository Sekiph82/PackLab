# M13-C001-R01 - PL-0299 Authority Resolution & Continuation Master V02

Milestone: **M13 - CAD/BREP & Engineering Export**
Accepted frontier: **PL-0289 through PL-0298 AUDITED_PASS**
Current child: **PL-0299 V02**
Remaining after closure: **PL-0300 through PL-0309**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/M13-C001_CHATGPT_PARTIAL_AUDIT_V01.md

PL-0299 V02:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0299_CODEX_PROMPT_V02.md

PL-0299 V02 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0299_CHATGPT_AUDIT_CRITERIA_V02.md

Continuation log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_PL0299_CONTINUATION_CODEX_LOG_V02.md

## Start rule

Synchronize safely and confirm live `TASKS.md` authorizes M13-C001-R01. Preserve accepted PL-0289 through PL-0298 implementation/evidence exactly.

## Phase A - PL-0299 V02

Execute PL-0299 V02 exactly.

The authority resolution is frozen:

- mandatory output is single-source OBJ + GLB from one exact CAD preview/tessellated Design Model source;
- M12 assembly hierarchy remains metadata-only;
- assembly/multipart geometry is not required and must not be fabricated;
- RELATIVE remains relative;
- mm_unverified remains unverified.

If PL-0299 V02 is green:

1. publish implementation/evidence commit(s);
2. publish separate `PL-0299_CODEX_LOG_V02.md` ending `READY_FOR_INDEPENDENT_AUDIT`;
3. update original master row and continuation log;
4. continue immediately to PL-0300.

## Phase B - Resume existing PL-0300 through PL-0309 V01 packages

Execute the already-published V01 prompts/criteria in exact order:

PL-0300 → PL-0301 → PL-0302 → PL-0303 → PL-0304 → PL-0305 → PL-0306 → PL-0307 → PL-0308 → PL-0309.

For each green child:

- implement only that child;
- run focused/predecessor/full/static/scope/security/dependency checks;
- publish implementation/evidence commit(s);
- publish separate child-log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`;
- verify remote visibility;
- update original M13 master log and this continuation log;
- continue automatically.

Do not wait for intermediate ChatGPT audit.

## Retained M13 gates

- CAD/BREP is derived Design Model engineering representation.
- CAPTURED_SCAN_MASTER and STANDALONE_DESIGN_GEOMETRY remain explicit.
- RELATIVE never silently becomes mm.
- mm_unverified remains physically unverified.
- PL-0220 through PL-0224 remain deferred.
- OCP/OCCT per-DLL native license/NOTICE inventory remains an installer/binary redistribution release gate.
- PL-0308 must stop if a new unreviewed PDF dependency is required.
- M14+ is unauthorized.

## Stop conditions

Stop on real validation failure, authority ambiguity, dependency/license/privacy issue, tracker/sync conflict, owner-required decision, or need to start M14.

On stop, publish exact blocker evidence and end continuation log `AWAITING_MILESTONE_AUDIT`.

## Successful final handoff

After PL-0309 green:

- original M13 master log must accurately cover PL-0289 through PL-0309;
- continuation log must record PL-0299 V02 resolution and PL-0300→0309 continuation;
- set `BATCH_COMPLETED`;
- verify clean local/origin/GitHub parity;
- confirm M14 not started;
- end exactly `AWAITING_MILESTONE_AUDIT`;
- stop for independent ChatGPT audit.
