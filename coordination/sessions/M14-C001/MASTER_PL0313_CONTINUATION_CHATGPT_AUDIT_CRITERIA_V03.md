# M14-C001-R02 - PL-0313 Continuation Master Audit Criteria V03

All criteria are mandatory.

1. PL-0310 through PL-0312 remain unchanged and independently accepted.
2. PL-0313 V02 introduces an explicit exact Label Metric Surface Binding rather than reinterpreting normalized UV as mm.
3. RELATIVE always fails closed; only METRIC_UNVERIFIED/mm_unverified produces numerical metric dielines and physical validation remains deferred.
4. FRONT/BACK PLANAR_RECTANGULAR mapping uses a uniquely resolved exact rectangular trimmed planar host surface; whole-solid bbox and transient face identity are forbidden substitutes.
5. WRAP CYLINDRICAL_WRAP uses exact cylinder radius/axis/extent plus accepted seam/orientation and deterministic arc-length flattening; ambiguity/unsupported trim fails closed.
6. Unsupported/freeform/non-developable mapping is not guessed or generically flattened.
7. PL-0314 through PL-0331 begin only after PL-0313 V02 is builder-green and execute in exact order under their frozen packages.
8. Label/artwork/geometry authority separation, material/PBR/PCR visual-only semantics and all physical/manufacturing/certification limitations remain intact.
9. PL-0324 remains a real Blender capability gate; no auto-download/bundling/fake substitution for mandatory real Blender evidence.
10. No M15+ implementation begins.
11. Every completed child has distinct implementation/evidence and log-only publication with terminal `READY_FOR_INDEPENDENT_AUDIT`.
12. Real blockers cause truthful `BATCH_STOPPED`; successful completion records `BATCH_COMPLETED`, clean parity, exact Blender facts, M15-not-started and terminal `AWAITING_MILESTONE_AUDIT`.

Independent audit must inspect actual source/diffs/evidence. Builder PASS claims are not acceptance.
