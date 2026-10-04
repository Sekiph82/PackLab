# M12-C001-R02 — Standalone Design Geometry Authority Resolution + PL-0283→PL-0288 Continuation

Milestone: **M12 - Advanced Packaging Geometry**
Accepted frontier: **PL-0268 through PL-0282**
Current task: **PL-0283 V02**
Remaining: **PL-0283 through PL-0288 V02**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/M12-C001_CHATGPT_PARTIAL_AUDIT_V02.md

Authority ADR:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0005-standalone-design-geometry-root.md

Master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_AUTHORITY_RESOLUTION_CONTINUATION_CHATGPT_AUDIT_CRITERIA_V03.md

Required continuation log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_AUTHORITY_RESOLUTION_CONTINUATION_CODEX_LOG_V03.md

## Starting frontier

At authorization time:

- PL-0268 through PL-0282 are independently AUDITED_PASS;
- PL-0283 V01 is a valid blocker, not an implementation failure;
- PL-0284 through PL-0288 were not started;
- no M13 implementation exists;
- physical validation remains deferred.

Do not reimplement PL-0268 through PL-0282.

## Mandatory synchronization

Fetch origin/main, verify root/remote/branch/worktree/divergence and fast-forward only when safe. Preserve owner-local work. Confirm live tracker authorizes M12-C001-R02. Stop on mismatch.

## Architecture resolution

Implement ADR-0005 exactly in spirit:

- existing scan-bound CAPTURED_SCAN_MASTER Design Models remain valid and backward compatible;
- add explicit STANDALONE_DESIGN_GEOMETRY root authority for model-only design;
- do not fabricate scan/reconstruction/digest/scale-provenance values;
- do not silently change accepted scan-bound revision IDs or canonical serialization;
- generic edit/history/validation/serialization/preview may support both parent modes;
- captured-only services must reject standalone models when captured evidence is required;
- physical validation and mold/manufacturing authority remain deferred/false.

The implementation design may use a discriminated parent union, versioned document contract extension or another clean approach, but must satisfy the V02 child criteria and backward-compatibility tests.

## Ordered execution

Execute, in order:

1. PL-0283 V02
2. PL-0284 V02
3. PL-0285 V02
4. PL-0286 V02
5. PL-0287 V02
6. PL-0288 V02

Use each V02 prompt and V02 audit criteria. For every green child:

- run focused/predecessor/full/static/scope/security checks;
- publish implementation/evidence commit(s);
- publish separate V02 child-log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`;
- verify remote visibility;
- update original M12 master log and R02 continuation log;
- continue immediately.

Do not wait for intermediate ChatGPT audit.

## Full-suite gate

Because PL-0283 changes a shared authority contract, require **two consecutive green exact locked full-suite runs** at the final PL-0283 authority-foundation revision before PL-0284 begins.

Subsequent children require their normal exact locked full-suite gate.

## Stop conditions

Stop on real validation failure, backward-compatibility break, authority ambiguity, dependency/license/privacy issue, owner-required choice or need to start M13.

On stop, publish exact blocker evidence, mark continuation BATCH_STOPPED, preserve earlier evidence and end the continuation log `AWAITING_MILESTONE_AUDIT`.

## Final handoff

After PL-0288 is green:

- original M12 master log must accurately cover PL-0268 through PL-0288;
- R02 continuation log must cover authority resolution and V02 remaining children;
- set `BATCH_COMPLETED`;
- verify local/origin/GitHub parity and clean execution worktree;
- confirm M13 not started;
- end exactly `AWAITING_MILESTONE_AUDIT`;
- stop for independent audit.
