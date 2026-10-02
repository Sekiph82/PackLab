# M10-C001 - Codex Master Work Order V01

Milestone: **M10 - Mesh Processing & Scan Master**
Ordered children: **PL-0225 through PL-0240**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

Required master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/MASTER_CODEX_LOG_V01.md

Accepted predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/M09-C001_CHATGPT_AUDIT_V01.md

Owner physical-validation deferral:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/M09_PHYSICAL_VALIDATION_DEFERRAL_OWNER_DECISION_V01.md

Mandatory Scan Master authority spec:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0233_SCAN_MASTER_AUTHORITY.md

## Owner-approved continuation

The owner has explicitly deferred PL-0220 through PL-0224 physical validation because the printer is unavailable and the required benchmark objects are not currently available.

Those tasks are **not passed**. They are parked as `DEFERRED_OWNER_VALIDATION`.

M10 is authorized to continue under strict authority preservation:

- no fabricated physical evidence;
- no silent METRIC_UNVERIFIED -> METRIC_VERIFIED promotion;
- no physical-accuracy or mold/manufacturing claim;
- any Scan Master created before deferred validation closes must carry:
  - inherited scale state;
  - exact scale provenance;
  - `physical_accuracy_validation_status=DEFERRED_OWNER_VALIDATION`;
  - `mold_use_authorized=false`;
  - known limitations/coverage gaps.

## Continuous batch rule

This is one continuous ordered Codex batch. Do not pause after a green child for ChatGPT audit.

For each child:
1. fetch/synchronize safely, only clean behind-only fast-forward;
2. read master + child prompt/criteria + mandatory pre-reads;
3. implement only that child;
4. run focused/predecessor/full/static/scope/security checks;
5. publish implementation/evidence commit(s);
6. publish a separate child-log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`;
7. verify remote visibility;
8. continue directly to the next child while green.

Stop only for a real FAILED/BLOCKED/OWNER_REQUIRED condition, unsafe dependency/license issue, branch/tracker mismatch, unavailable mandatory capability, or need to start M11.

## Open3D gate

PL-0225 owns exact Open3D selection and pinning.

Before downstream M10 children rely on it, Codex must prove:
- Python 3.12 compatibility;
- Windows compatibility for the actual PackLab environment;
- exact package/version/build in the lockfile;
- successful import/capability probe;
- PackLab-owned adapter boundary;
- exact license/register update for the selected artifact.

If no compatible reviewed package exists, stop at PL-0225 as BLOCKED. Do not fake an Open3D capability and do not substitute another unapproved geometry stack silently.

## Ordered children

1. **PL-0225** — Integrate Open3D as the primary point-cloud/mesh analysis utility layer.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0225_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0225_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0225_CODEX_LOG_V01.md

2. **PL-0226** — Remove isolated floating components with configurable safeguards.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0226_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0226_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0226_CODEX_LOG_V01.md

3. **PL-0227** — Implement normal estimation/orientation repair.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0227_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0227_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0227_CODEX_LOG_V01.md

4. **PL-0228** — Implement conservative smoothing that preserves packaging edges.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0228_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0228_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0228_CODEX_LOG_V01.md

5. **PL-0229** — Implement hole detection and report hole size/location before any repair.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0229_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0229_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0229_CODEX_LOG_V01.md

6. **PL-0230** — Implement optional hole filling with non-destructive before/after versions.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0230_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0230_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0230_CODEX_LOG_V01.md

7. **PL-0231** — Implement decimation for viewport/proxy meshes while preserving the Scan Master.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0231_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0231_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0231_CODEX_LOG_V01.md

8. **PL-0232** — Compute geometric statistics needed by later fitting stages.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0232_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0232_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0232_CODEX_LOG_V01.md

9. **PL-0233** — Create Scan Master asset with captured-evidence-only ancestry and provenance.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0233_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0233_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0233_CODEX_LOG_V01.md

10. **PL-0234** — Implement point-cloud/mesh registration for comparing repeat scans.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0234_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0234_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0234_CODEX_LOG_V01.md

11. **PL-0235** — Implement distance heatmap between scan and fitted Design Model.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0235_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0235_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0235_CODEX_LOG_V01.md

12. **PL-0236** — Implement cross-section comparison overlay.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0236_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0236_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0236_CODEX_LOG_V01.md

13. **PL-0237** — Record reconstruction versions and allow switching between them.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0237_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0237_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0237_CODEX_LOG_V01.md

14. **PL-0238** — Add Promote to Scan Master action with audit metadata and hard authority gate.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0238_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0238_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0238_CODEX_LOG_V01.md

15. **PL-0239** — Prevent downstream Design Model from silently changing when reconstruction is rerun.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0239_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0239_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0239_CODEX_LOG_V01.md

16. **PL-0240** — Add Scan Master export as PLY/OBJ/GLB plus original texture assets.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0240_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0240_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0240_CODEX_LOG_V01.md

## Authority invariants

- RAW_CAPTURE is immutable.
- Original reconstruction and OBJECT_CAPTURE_GEOMETRY are immutable parents.
- Cleanup creates new revisions.
- AI_VISUAL_REFERENCE/generated geometry is ineligible for Scan Master.
- PREVIEW_PROXY is never Scan Master.
- Hole filling and smoothing must remain bounded, explicit and provenance-recorded.
- Scan Master can exist with inherited METRIC_UNVERIFIED scale, but then physical validation remains deferred and mold use is unauthorized.
- M10 Scan Master authority is captured-geometry workflow authority, not a statement of manufacturing accuracy.
- Future Design Model bindings pin exact Scan Master IDs; newer reconstruction/Scan Master revisions never silently retarget them.
- M11 is unauthorized during this batch.

## Batch stop publication

If blocked:
1. publish current child blocker/evidence log;
2. update master log with `BATCH_STOPPED`;
3. record exact child/reason;
4. preserve all earlier green child evidence;
5. end master log exactly `AWAITING_MILESTONE_AUDIT`;
6. stop.

## Successful final handoff

After PL-0240 is green:
1. set master status `BATCH_COMPLETED`;
2. publish final master log separately;
3. verify local/origin/GitHub main parity and clean worktree;
4. confirm M11 was not started;
5. end exactly:

`AWAITING_MILESTONE_AUDIT`
