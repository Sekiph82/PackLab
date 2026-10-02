# M09-C001 - Codex Master Work Order V01

Milestone: **M09 - Scale, Calibration & Measurement**
Ordered children: **PL-0202 through PL-0224**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

This master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/MASTER_CODEX_PROMPT_V01.md

Master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

Required master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/MASTER_CODEX_LOG_V01.md

Accepted predecessor:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/M08-C001_CHATGPT_AUDIT_V02.md

## Batch operating rule

This is one continuous ordered Codex batch. Do not pause after a green child for an intermediate ChatGPT audit.

For every child:

1. verify Git root, branch `main`, remote and clean/behind-only synchronization;
2. read the matching child prompt/criteria and mandatory pre-reads;
3. implement only that child;
4. run focused/regression/full/static/scope/security checks;
5. publish implementation/evidence commit(s);
6. publish a separate child-log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`;
7. verify remote visibility;
8. continue directly to the next child if green and no real stop condition exists.

Independent child/milestone audit occurs after the batch handoff.

## Existing calibration foundation

M09 must reuse rather than casually replace the accepted calibration foundation:

- PackLab AprilTag marker policy/detection;
- synthetic calibration ground truth;
- scale-estimation math and confidence policy;
- calibration mat source assets;
- owner-controlled printed-mat verification procedure;
- accepted M08 OBJECT_CAPTURE_GEOMETRY and mask/revision authority;
- mandatory PL-0209 metric-scale provenance specification.

Mandatory architecture rule:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0209_METRIC_SCALE_PROVENANCE.md

A reconstruction coordinate is not millimetres merely because a backend, image-space mm/pixel estimate, neural model, AR world unit or nominal SVG says so.

## Physical evidence and PL-0068

PL-0068 remains separately `OWNER_REQUIRED` because the accepted physical printed-mat verification/capture evidence has not been supplied.

That open gate **does not block code-only/synthetic implementation children** PL-0202 onward.

It does mean:

- no child may silently claim owner print verification;
- no nominal mat dimension may masquerade as measured print geometry;
- no synthetic fixture may promote a real project to `METRIC_VERIFIED`;
- physical benchmark children must stop truthfully when their owner-controlled evidence is absent.

Expected hard physical gates are especially PL-0220, PL-0222 and PL-0223. If required evidence is unavailable, that is a correct `OWNER_REQUIRED` frontier, not a reason to fabricate results.

## Ordered child package

1. **PL-0202** — Detect calibration markers in source imagery and associate observations with reconstructed cameras.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0202_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0202_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0202_CODEX_LOG_V01.md

2. **PL-0203** — Estimate global scale from marker geometry and reject inconsistent observations.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0203_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0203_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0203_CODEX_LOG_V01.md

3. **PL-0204** — Establish canonical PackLab axes: Z up, front direction, millimetres.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0204_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0204_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0204_CODEX_LOG_V01.md

4. **PL-0205** — Implement object ground-plane/base detection with user override.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0205_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0205_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0205_CODEX_LOG_V01.md

5. **PL-0206** — Implement automatic upright alignment with manual correction.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0206_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0206_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0206_CODEX_LOG_V01.md

6. **PL-0207** — Implement front-direction selection and persist it as project metadata.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0207_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0207_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0207_CODEX_LOG_V01.md

7. **PL-0208** — Apply scale/alignment as non-destructive transform before baking a normalized scan.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0208_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0208_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0208_CODEX_LOG_V01.md

8. **PL-0209** — Record scale provenance, uncertainty and explicit RELATIVE/METRIC_UNVERIFIED/METRIC_VERIFIED state.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0209_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0209_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0209_CODEX_LOG_V01.md

9. **PL-0210** — Implement bounding dimensions: height, width and depth.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0210_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0210_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0210_CODEX_LOG_V01.md

10. **PL-0211** — Implement two-point distance measurement with snapping.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0211_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0211_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0211_CODEX_LOG_V01.md

11. **PL-0212** — Implement diameter/radius measurement from selected cross-sections.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0212_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0212_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0212_CODEX_LOG_V01.md

12. **PL-0213** — Implement horizontal cross-section extraction at arbitrary Z.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0213_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0213_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0213_CODEX_LOG_V01.md

13. **PL-0214** — Implement vertical profile/silhouette extraction.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0214_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0214_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0214_CODEX_LOG_V01.md

14. **PL-0215** — Implement neck/finish candidate measurement.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0215_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0215_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0215_CODEX_LOG_V01.md

15. **PL-0216** — Implement capacity-estimation groundwork using watertight interior assumptions, clearly separating estimate from certified volume.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0216_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0216_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0216_CODEX_LOG_V01.md

16. **PL-0217** — Display measurement uncertainty/confidence where known.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0217_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0217_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0217_CODEX_LOG_V01.md

17. **PL-0218** — Export measurement report with units and provenance.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0218_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0218_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0218_CODEX_LOG_V01.md

18. **PL-0219** — Define physical benchmark set with caliper-measured ground truth.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0219_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0219_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0219_CODEX_LOG_V01.md

19. **PL-0220** — Measure dimension error across at least matte bottle, glossy bottle and jerrycan.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0220_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0220_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0220_CODEX_LOG_V01.md

20. **PL-0221** — Establish V1 acceptance thresholds for overall dimensions and key features.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0221_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0221_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0221_CODEX_LOG_V01.md

21. **PL-0222** — Add repeat-scan reproducibility test for the same object.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0222_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0222_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0222_CODEX_LOG_V01.md

22. **PL-0223** — Add calibration-mat print-scale sensitivity test.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0223_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0223_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0223_CODEX_LOG_V01.md

23. **PL-0224** — Document conditions under which PackLab measurements must not be used for mold manufacturing.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0224_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0224_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0224_CODEX_LOG_V01.md

## Critical architecture rules

- RAW_CAPTURE and accepted M08 artifacts remain immutable.
- `AI_VISUAL_REFERENCE` never gains measurement authority.
- Only M09 calibration logic may promote scale state, and `METRIC_VERIFIED` requires accepted physical evidence.
- The existing image-space calibration `mm_per_pixel` estimator is not by itself a global 3D reconstruction scale.
- Scale, upright and front normalization remain non-destructive until an explicitly versioned normalized captured-geometry artifact is produced.
- Measurement outputs bind exact normalized geometry, scale provenance, units, method/version and uncertainty.
- RELATIVE geometry must never be labeled millimetres.
- Capacity remains estimate-only under explicit interior/watertight assumptions and is never certified volume.
- Physical benchmark data must be owner-controlled, revision-bound and truthful. Missing evidence stays missing.
- M09 must not create SCAN_MASTER, execute M10 cleanup, or claim mold-manufacturing suitability beyond benchmark evidence.

## Stop conditions

Stop the whole batch at the current child on:

- validation failure not correctable inside the frozen child;
- tracker/branch/synchronization mismatch;
- architecture/provenance/authority conflict;
- missing mandatory pre-read or capability;
- privacy/security/license issue;
- need for owner-controlled physical evidence that is unavailable;
- need to start M10/later work.

On stop:

1. publish the current child blocker/evidence log;
2. update the master log with `BATCH_STOPPED`;
3. record exact frontier and reason;
4. use a specific status such as `OWNER_REQUIRED_PHYSICAL_BENCHMARK_EVIDENCE` when applicable;
5. preserve all earlier green child evidence;
6. end the master log exactly `AWAITING_MILESTONE_AUDIT`;
7. stop.

Do not continue to later children after a blocked frontier.

## Final handoff

If PL-0224 completes green:

1. record `BATCH_COMPLETED`;
2. publish the completed master log separately;
3. verify local/origin/GitHub `main` parity and clean worktree;
4. confirm M10 was not started;
5. end the master log exactly:

`AWAITING_MILESTONE_AUDIT`
