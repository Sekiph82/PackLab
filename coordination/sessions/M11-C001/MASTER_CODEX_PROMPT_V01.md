# M11-C001 - Codex Master Work Order V01

Milestone: **M11 - Parametric Geometry Engine V1**
Ordered children: **PL-0241 through PL-0267**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

Required master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/MASTER_CODEX_LOG_V01.md

Accepted predecessor:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/M10-C001_CHATGPT_AUDIT_V01.md

Owner physical-validation deferral:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/M09_PHYSICAL_VALIDATION_DEFERRAL_OWNER_DECISION_V01.md

Scan Master authority:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0233_SCAN_MASTER_AUTHORITY.md

## Batch operating rule

This is one continuous ordered Codex batch. Do not pause after a green child for an intermediate ChatGPT audit.

For every child:
1. verify Git root, branch/main target, remote and clean/behind-only synchronization;
2. read master + child prompt/criteria + mandatory pre-reads;
3. implement only that child;
4. run focused/predecessor/full/static/scope/security checks;
5. publish implementation/evidence commit(s);
6. publish a separate child-log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`;
7. verify remote visibility;
8. update the master table with exact SHAs/results;
9. continue directly to the next child while green.

Independent child/milestone audit occurs only after the batch handoff.

## Design Model authority

M11 creates PackLab's editable parametric **DESIGN_MODEL** authority. It is separate from captured geometry:

```text
SCAN_MASTER (captured reference)
  -> pinned parent binding
  -> DESIGN_MODEL parameter graph
  -> derived preview mesh / comparison evidence
```

Rules:

- Scan Master is immutable input/reference and is never rewritten by Design Model edits.
- Design Model truth lives in versioned human-readable parameters/features/operations, not triangle preview meshes.
- Preview/tessellated meshes are derived/disposable and may not become Scan Master or parametric truth.
- Every fitted Design Model revision pins one exact Scan Master revision/digest.
- Newer reconstruction or Scan Master revisions never silently retarget an existing Design Model.
- Stable feature IDs must not depend on transient preview vertex/triangle indices.
- M13 CAD/BREP/OpenCascade APIs are out of scope; M11 abstractions must remain backend-neutral.

## Deferred physical-validation rule

PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`, not passed.

Therefore:

- inherited `METRIC_UNVERIFIED` remains unverified;
- when coordinates derive from that state, use explicit `mm_unverified` semantics rather than verified millimetres;
- no M11 fit/deviation/dimension may claim manufacturing tolerance, mold readiness, certification or physical benchmark acceptance;
- no fitting quality score can substitute for the deferred physical benchmark;
- closure/neck models must not infer invisible thread/seal/internal engineering truth.

This limitation must travel with Design Model revisions, previews, reports and assembly metadata.

## Ordered child package

1. **PL-0241** — Define Design Model parameter graph separate from triangle-mesh data.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0241_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0241_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0241_CODEX_LOG_V01.md

2. **PL-0242** — Define feature IDs and stable references for body, base, shoulder, neck, finish and cap.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0242_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0242_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0242_CODEX_LOG_V01.md

3. **PL-0243** — Implement spline/profile primitives with millimetre coordinates.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0243_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0243_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0243_CODEX_LOG_V01.md

4. **PL-0244** — Implement editable cross-section primitive with symmetry options.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0244_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0244_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0244_CODEX_LOG_V01.md

5. **PL-0245** — Implement loft/revolve abstraction independent of final CAD backend.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0245_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0245_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0245_CODEX_LOG_V01.md

6. **PL-0246** — Implement parameter validation and impossible-geometry rejection.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0246_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0246_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0246_CODEX_LOG_V01.md

7. **PL-0247** — Implement undo/redo command model for parametric edits.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0247_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0247_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0247_CODEX_LOG_V01.md

8. **PL-0248** — Serialize Design Model parameters in a versioned human-readable project format.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0248_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0248_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0248_CODEX_LOG_V01.md

9. **PL-0249** — Generate tessellated preview mesh from parameters for interactive viewport use.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0249_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0249_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0249_CODEX_LOG_V01.md

10. **PL-0250** — Detect rotational/symmetry characteristics and choose bottle fitting strategy.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0250_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0250_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0250_CODEX_LOG_V01.md

11. **PL-0251** — Extract robust vertical body profile from normalized Scan Master.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0251_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0251_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0251_CODEX_LOG_V01.md

12. **PL-0252** — Fit smoothed profile while preserving shoulder/base transitions.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0252_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0252_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0252_CODEX_LOG_V01.md

13. **PL-0253** — Detect body, shoulder, neck and base zones with editable boundaries.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0253_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0253_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0253_CODEX_LOG_V01.md

14. **PL-0254** — Generate revolved Design Model for axisymmetric bottle/jar.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0254_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0254_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0254_CODEX_LOG_V01.md

15. **PL-0255** — Fit non-circular but symmetric body using stacked cross-sections and lofting.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0255_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0255_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0255_CODEX_LOG_V01.md

16. **PL-0256** — Add front/back and left/right symmetry constraints with user toggle.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0256_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0256_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0256_CODEX_LOG_V01.md

17. **PL-0257** — Calculate scan-to-design deviation and expose problem regions.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0257_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0257_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0257_CODEX_LOG_V01.md

18. **PL-0258** — Allow user to edit height/width/depth while maintaining parameter relationships.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0258_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0258_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0258_CODEX_LOG_V01.md

19. **PL-0259** — Allow direct profile/cross-section control-point editing.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0259_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0259_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0259_CODEX_LOG_V01.md

20. **PL-0260** — Save fitting preset and parameters independently of the raw scan.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0260_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0260_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0260_CODEX_LOG_V01.md

21. **PL-0261** — Separate cap/closure from body when scan evidence allows.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0261_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0261_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0261_CODEX_LOG_V01.md

22. **PL-0262** — Fit basic cylindrical screw-cap exterior.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0262_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0262_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0262_CODEX_LOG_V01.md

23. **PL-0263** — Fit flip-top/simple closure exterior as an editable component.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0263_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0263_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0263_CODEX_LOG_V01.md

24. **PL-0264** — Define neck/closure mating reference planes and axes.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0264_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0264_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0264_CODEX_LOG_V01.md

25. **PL-0265** — Add cap visibility/replacement workflow.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0265_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0265_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0265_CODEX_LOG_V01.md

26. **PL-0266** — Add closure dimensions to measurement report.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0266_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0266_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0266_CODEX_LOG_V01.md

27. **PL-0267** — Validate bottle/cap assembly transforms on export.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0267_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0267_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0267_CODEX_LOG_V01.md

## Critical scope boundaries

- M11 owns common parametric kernel, bottle/jar fitting and basic closure exteriors only.
- M12 advanced jerrycan handles, pumps/triggers, tubes/sachets and freeform/cage work are unauthorized.
- M13 CAD/BREP/STEP/STL engineering export is unauthorized.
- No new CAD kernel/binding dependency may be introduced.
- No AI/generated geometry may silently become captured or parametric evidence.
- Fitting presets may contain reusable parameters, never private/raw scan bytes.
- Scan-to-design comparisons must reuse accepted M10 authority gates rather than weakening them.
- UI layers delegate domain truth to core services.

## Stop conditions

Stop the whole batch on:
- validation failure not correctable within the frozen child;
- tracker/branch/synchronization mismatch;
- architecture/provenance/authority conflict;
- missing mandatory capability/pre-read;
- privacy/security/license issue;
- owner decision required;
- need to start M12/later work.

On stop:
1. publish the current child blocker/evidence log;
2. update master log `BATCH_STOPPED`;
3. record exact child/reason;
4. preserve earlier green evidence;
5. end master log exactly `AWAITING_MILESTONE_AUDIT`;
6. stop.

## Final handoff

If PL-0267 completes green:
1. set `BATCH_COMPLETED`;
2. publish the completed master log separately;
3. verify local/origin/GitHub `main` parity and clean worktree;
4. confirm M12 was not started;
5. end exactly:

`AWAITING_MILESTONE_AUDIT`
