# M14-C001-R02 - PL-0313 Metric Mapping Resolution & Continuation Master V03

Milestone: **M14 - Labels, Materials & Rendering**
Independently accepted frontier: **PL-0310 through PL-0312**
Current child: **PL-0313 V02**
Remaining after closure: **PL-0314 through PL-0331**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/M14-C001_CHATGPT_PARTIAL_AUDIT_V02.md

PL-0313 V02:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0313_CODEX_PROMPT_V02.md

PL-0313 V02 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0313_CHATGPT_AUDIT_CRITERIA_V02.md

Master criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/MASTER_PL0313_CONTINUATION_CHATGPT_AUDIT_CRITERIA_V03.md

Continuation log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/MASTER_PL0313_CONTINUATION_CODEX_LOG_V03.md

## Start rule

1. Synchronize the execution checkout non-destructively with latest `origin/main`.
2. Preserve owner-local work and unrelated checkouts.
3. Verify live root `TASKS.md` authorizes M14-C001-R02.
4. Read M14 partial audit V02 and PL-0313 V02 prompt/criteria.
5. Preserve accepted PL-0310→PL-0312 source/evidence exactly.
6. Confirm M15+ remains unauthorized.

Root `TASKS.md` lifecycle is ChatGPT-owned. Codex must not edit it.

## Phase A - PL-0313 V02

Execute PL-0313 V02 exactly.

Frozen resolution:

- normalized Label Zone UV is not itself metric authority;
- metric output requires an explicit exact Label Metric Surface Binding;
- only METRIC_UNVERIFIED/mm_unverified may emit mm dielines;
- RELATIVE fails closed;
- FRONT/BACK support is PLANAR_RECTANGULAR only;
- WRAP support is exact CYLINDRICAL_WRAP only;
- host-surface resolution must be exact/deterministic against pinned BREP + selected PL-0312 region evidence;
- native/transient face identity cannot become persisted authority;
- unsupported/freeform mapping fails closed.

If PL-0313 V02 closes green:

1. publish implementation/evidence commit(s);
2. publish separate `PL-0313_CODEX_LOG_V02.md` ending exactly `READY_FOR_INDEPENDENT_AUDIT`;
3. update original M14 master index and this continuation log;
4. continue immediately to PL-0314.

## Phase B - Continue PL-0314 through PL-0331

Execute the already-published V01 child prompt/criteria packages in exact order:

PL-0314 → PL-0315 → PL-0316 → PL-0317 → PL-0318 → PL-0319 → PL-0320 → PL-0321 → PL-0322 → PL-0323 → PL-0324 → PL-0325 → PL-0326 → PL-0327 → PL-0328 → PL-0329 → PL-0330 → PL-0331.

For every green child:

- read its exact prompt and criteria before coding;
- implement only that child and accepted predecessor seams;
- run its focused/predecessor checks, locked full suite and mandated static/security/dependency checks;
- publish implementation/evidence commit(s);
- publish a distinct child-log-only commit ending exactly `READY_FOR_INDEPENDENT_AUDIT`;
- verify remote visibility and local/origin/GitHub parity;
- update the original M14 master log and this continuation log;
- continue automatically while all mandatory gates remain green.

Do not wait for intermediate ChatGPT audit.

## Retained authority rules

- Label Zone remains independent of artwork.
- Label metric mapping/dielines remain derived design geometry, never physical calibration.
- RELATIVE never becomes mm.
- mm_unverified remains physically unverified.
- PL-0314 safe/bleed values are design/print-intent metadata, not printer certification.
- Artwork import/mapping never becomes geometry authority.
- Material/PBR/PCR remains visual/design metadata absent separately accepted certification authority.
- Render/export success never implies print-fit, manufacturing, mold, material certification, regulatory approval or physical accuracy.
- M13 CAD authority remains unchanged.
- M15+ is unauthorized.

## Blender capability gate

PL-0324 remains a real capability gate.

No Blender auto-download, committed binary, hidden installer fetch or runtime network dependency is allowed.

If no usable approved real Blender executable exists, stop truthfully at the gate. For Blender-dependent children, unit fakes may supplement but cannot replace required real headless import/render/export evidence.

## Stop conditions

Stop immediately on any:

- unresolved authority ambiguity;
- unsupported mapping required by the child;
- RELATIVE→mm escalation;
- physical/material/manufacturing/certification authority escalation;
- malformed/unbounded asset handling;
- dependency/license/privacy/security issue;
- need for unreviewed dependency;
- runtime network/download requirement;
- real Blender capability failure;
- locked-suite failure not truthfully proven unrelated;
- tracker/sync conflict;
- owner-required decision;
- M15+ work.

On stop, record exact blocker, set `BATCH_STOPPED`, end continuation log exactly `AWAITING_MILESTONE_AUDIT`, and stop.

## Successful final handoff

If PL-0331 closes green:

- original M14 master log accurately covers PL-0310→PL-0331;
- this continuation log records PL-0313 V02 resolution and PL-0314→0331 continuation;
- record all child implementation/evidence and log SHAs;
- record `BATCH_COMPLETED`;
- verify clean local/origin/GitHub parity;
- record exact real Blender executable/version/build facts used;
- confirm M15 started: NO;
- preserve all physical/material/certification limitations;
- end exactly `AWAITING_MILESTONE_AUDIT`;
- stop for independent ChatGPT milestone audit.
