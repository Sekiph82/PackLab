# M08-C001 - Remaining Batch Codex Master Work Order V02

Milestone: **M08 - Segmentation, Object Extraction & Reconstruction QA**
Accepted children already closed: **PL-0184 through PL-0187**
Ordered remaining children: **PL-0188 through PL-0201**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

This master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/MASTER_REMAINING_CODEX_PROMPT_V02.md

Master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/MASTER_REMAINING_CHATGPT_AUDIT_CRITERIA_V02.md

Required master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/MASTER_REMAINING_CODEX_LOG_V02.md

Accepted predecessor frontier:
- PL-0184 AUDITED_PASS
- PL-0185 AUDITED_PASS
- PL-0186 AUDITED_PASS
- PL-0187 AUDITED_PASS
Latest accepted audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CHATGPT_AUDIT_V02.md

## Batch operating rule

This is one continuous Codex batch.

Do **not** stop after a validation-green child to wait for ChatGPT audit.

For every child:
1. synchronize safely with `origin/main`;
2. read that child's prompt and audit criteria;
3. implement only that child;
4. run the required focused/regression/full/static/scope checks;
5. create an implementation/evidence commit;
6. create a separate child-log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`;
7. verify the log is remotely visible;
8. if all frozen gates are green and no stop condition exists, continue immediately to the next ordered child.

Independent ChatGPT audits happen after the remaining batch handoff.

Stop the whole batch only on a real:
- FAILED validation that cannot be corrected within the current child;
- BLOCKED architecture/spec/capability condition;
- OWNER_REQUIRED decision;
- privacy/security/license problem;
- tracker/branch/synchronization mismatch;
- need to start M09/later work.

On stop, publish the current child log plus the master log with exact frontier and `BATCH_STOPPED`.

## Exact remaining child order and canonical files

1. **PL-0188** - manual mask-correction UI and revision handoff  
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0188_CODEX_PROMPT_V03.md  
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0188_CHATGPT_AUDIT_CRITERIA_V03.md  
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0188_CODEX_LOG_V03.md

2. **PL-0189** - independent mask revisions and downstream geometry invalidation  
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0189_CODEX_PROMPT_V01.md  
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0189_CHATGPT_AUDIT_CRITERIA_V01.md  
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0189_CODEX_LOG_V01.md

3. **PL-0190** - mask-to-3D lifting and OBJECT_CAPTURE_GEOMETRY  
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0190_CODEX_PROMPT_V01.md  
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0190_CHATGPT_AUDIT_CRITERIA_V01.md  
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0190_CODEX_LOG_V01.md  
   Mandatory pre-reads: `docs/implementation/PL-0190_OBJECT_MASK_LIFT_MULTIVIEW_FUSION.md`, `docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md`, and `docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md`.

4. **PL-0191** - mask-quality overlays/contact sheets  
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0191_CODEX_PROMPT_V01.md  
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0191_CHATGPT_AUDIT_CRITERIA_V01.md  
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0191_CODEX_LOG_V01.md

5. **PL-0192** - pre-reconstruction QA report  
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0192_CODEX_PROMPT_V01.md  
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0192_CHATGPT_AUDIT_CRITERIA_V01.md  
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0192_CODEX_LOG_V01.md

6. **PL-0193** - duplicate/near-duplicate detection  
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0193_CODEX_PROMPT_V01.md  
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0193_CHATGPT_AUDIT_CRITERIA_V01.md  
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0193_CODEX_LOG_V01.md

7. **PL-0194** - focal/lens consistency warnings  
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0194_CODEX_PROMPT_V01.md  
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0194_CHATGPT_AUDIT_CRITERIA_V01.md  
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0194_CODEX_LOG_V01.md

8. **PL-0195** - registered-photo ratio  
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0195_CODEX_PROMPT_V01.md  
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0195_CHATGPT_AUDIT_CRITERIA_V01.md  
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0195_CODEX_LOG_V01.md

9. **PL-0196** - sparse connectivity/fragmentation diagnostics  
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0196_CODEX_PROMPT_V01.md  
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0196_CHATGPT_AUDIT_CRITERIA_V01.md  
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0196_CODEX_LOG_V01.md

10. **PL-0197** - dense/object coverage and support indicators  
    Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0197_CODEX_PROMPT_V01.md  
    Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0197_CHATGPT_AUDIT_CRITERIA_V01.md  
    Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0197_CODEX_LOG_V01.md

11. **PL-0198** - reconstruction artifact/floating-component diagnostics  
    Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0198_CODEX_PROMPT_V01.md  
    Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0198_CHATGPT_AUDIT_CRITERIA_V01.md  
    Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0198_CODEX_LOG_V01.md

12. **PL-0199** - explainable reconstruction confidence  
    Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0199_CODEX_PROMPT_V01.md  
    Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0199_CHATGPT_AUDIT_CRITERIA_V01.md  
    Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0199_CODEX_LOG_V01.md

13. **PL-0200** - downstream parametric-fit quality gate  
    Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0200_CODEX_PROMPT_V01.md  
    Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0200_CHATGPT_AUDIT_CRITERIA_V01.md  
    Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0200_CODEX_LOG_V01.md

14. **PL-0201** - evidence-linked recapture-sector suggestions  
    Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0201_CODEX_PROMPT_V01.md  
    Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0201_CHATGPT_AUDIT_CRITERIA_V01.md  
    Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0201_CODEX_LOG_V01.md

## Inherited architecture

Treat PL-0184 through PL-0187 as frozen accepted foundations.

In particular:
- mask/model contracts remain backend-neutral;
- SAM 2.1 backend provenance remains accepted and may not be casually changed;
- post-processing remains deterministic/versioned;
- any consumer deriving content from an in-memory parent mask raster must verify the raster bytes correspond to the declared mask digest;
- RAW_CAPTURE remains immutable;
- UI remains presentation only;
- masks remain derived authority;
- M08 may create OBJECT_CAPTURE_GEOMETRY but not SCAN_MASTER or metric verification;
- AI_VISUAL_REFERENCE cannot substitute for captured geometry.

## Commit/evidence discipline

Each child must retain a separate implementation/evidence commit and separate log-only commit.

The child log ends `READY_FOR_INDEPENDENT_AUDIT`, but this marker is a publication/evidence boundary, **not a command to pause the batch**.

The master log indexes every child:
- child status;
- implementation SHA(s);
- log-only SHA;
- exact GitHub prompt/criteria/log URLs;
- focused/full validation result;
- limitations;
- next frontier.

## Final handoff

After PL-0201 is green and remotely visible:
1. update the master log with `BATCH_COMPLETED`;
2. publish the master log as a separate log-only commit;
3. verify local/main/origin/GitHub synchronization;
4. end the master log exactly with `AWAITING_MILESTONE_AUDIT`;
5. stop.

Do not start M09.
