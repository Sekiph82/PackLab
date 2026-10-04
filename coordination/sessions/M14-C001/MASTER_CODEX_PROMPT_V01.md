# M14-C001 - Labels, Materials & Rendering Master Codex Prompt V01

Milestone: **M14 - Labels, Materials & Rendering**
Ordered batch: **PL-0310 through PL-0331**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

Master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/MASTER_CODEX_LOG_V01.md

## Start rule

Before any implementation:

1. synchronize the execution checkout non-destructively with latest `origin/main`;
2. preserve owner-local work and do not touch unrelated checkouts;
3. verify live root `TASKS.md` authorizes M14-C001;
4. read the M13 final audit, M09 physical-validation deferral, ADR-0005 and this master package;
5. confirm M15+ remains unauthorized.

Root `TASKS.md` lifecycle is ChatGPT-owned. Codex must not edit it.

## Execution order

Execute exactly:

PL-0310 → PL-0311 → PL-0312 → PL-0313 → PL-0314 → PL-0315 → PL-0316 → PL-0317 → PL-0318 → PL-0319 → PL-0320 → PL-0321 → PL-0322 → PL-0323 → PL-0324 → PL-0325 → PL-0326 → PL-0327 → PL-0328 → PL-0329 → PL-0330 → PL-0331.

For each child:

- read its V01 prompt and V01 ChatGPT audit criteria before coding;
- implement only that child and accepted predecessor seams;
- run all child-mandated focused/predecessor tests plus the locked full suite and static/scope/security/dependency checks;
- publish implementation/evidence commit(s);
- publish a separate `PL-xxxx_CODEX_LOG_V01.md` log-only commit ending exactly `READY_FOR_INDEPENDENT_AUDIT`;
- verify remote visibility and local/origin/GitHub parity;
- update this master log row;
- continue automatically to the next child while all mandatory gates remain green.

Do not wait for intermediate ChatGPT audit unless a stop condition fires.

## Frozen M14 authority contract

- Label Zone is geometric/design placement metadata independent of artwork.
- Artwork is separate, digest-bound presentation content and never becomes geometry authority.
- Design Model/CAD revisions and stable semantic component/feature IDs remain geometric authority.
- RELATIVE/reconstruction_units never silently becomes millimetres.
- mm_unverified may carry numerical millimetres only with explicit physical-unverified status.
- Label dielines in millimetres must fail closed for RELATIVE sources.
- Material/PBR/PCR data is visual/design metadata unless separately backed by explicit accepted external certification authority.
- Render, PDF/image, SVG/DXF, GLB or Blender success never implies print-fit, mold, manufacturing, regulatory, recycled-content certification, material performance or physical accuracy.
- Blender is an external executable capability. No auto-download, committed binary, hidden installer fetch or runtime network dependency is permitted.
- M13 accepted source authority must not be replaced or mutated.

## Blender capability gate

PL-0324 is a real capability gate.

If no usable real Blender executable is available under the accepted discovery/version policy:

- complete only truthful discovery/probe implementation/evidence that can be supported;
- record exact blocker;
- do not claim Blender READY;
- stop the master before any child that requires real Blender execution;
- set batch status `BATCH_STOPPED` and terminal master log `AWAITING_MILESTONE_AUDIT`.

For PL-0326 through PL-0331, unit fakes may supplement tests but may not replace required real headless import/render/export evidence.

## Stop conditions

Stop immediately on any:

- source-authority ambiguity;
- RELATIVE→mm escalation;
- physical/material/production authority escalation;
- malformed/unbounded unsafe artwork or asset handling;
- dependency/license/privacy/security issue;
- need for an unreviewed dependency;
- network/runtime download requirement;
- real Blender capability failure where real execution is required;
- locked full-suite failure not truthfully proven unrelated;
- tracker/synchronization conflict;
- owner-required decision;
- need to start M15+.

Publish exact blocker evidence rather than inventing PASS.

## Successful final handoff

If PL-0331 closes green:

- master log contains all 22 child rows as `READY_FOR_INDEPENDENT_AUDIT`;
- record `BATCH_COMPLETED`;
- record final local/origin/GitHub SHA parity and clean worktree;
- record exact Blender version/build/executable capability used for real Blender children;
- record that M15 was not started;
- preserve all physical/material/certification limitations;
- end master log exactly `AWAITING_MILESTONE_AUDIT`;
- stop for independent ChatGPT milestone audit.

If stopped earlier, record `BATCH_STOPPED`, exact accepted/pending frontier and blocker, end exactly `AWAITING_MILESTONE_AUDIT`, and stop.
