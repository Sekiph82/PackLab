# PL-0190 - ChatGPT Audit Criteria V01

Task: **Lift object masks into OBJECT_CAPTURE_GEOMETRY with multiview consensus**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0190_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. The live tracker authorized the complete M08-C001 batch and this exact child frontier before implementation; predecessor evidence and mandatory pre-reads were present.
2. The implementation is PackLab-owned, deterministic, provenance-bound and limited to the frozen scope: Implement the explicit post-reconstruction object-extraction stage. Validate camera convention with a synthetic known point and normalize it; project world candidates through intrinsics, reject behind-camera/out-of-frame points, perform deterministic visibility before mask voting, record bounded observed/support/reject aggregates and threshold profile, retain reproducible unfiltered selection, optionally apply conservative outlier removal, and produce a preliminary QA OBB. Emit OBJECT_CAPTURE_GEOMETRY with generated=false, inherited scale limitations, parent reconstruction/camera/source/mask identities and complete invalidation dependencies.
3. Required negative, boundary, failure and regression behavior is tested through the public boundary: Use synthetic cameras/points for support, visible reject, occluded not-observed, behind-camera, out-of-frame, threshold boundary, iteration-order determinism, mask/reconstruction/camera revision invalidation, source bytes, generated flag and pre-M09 metric rejection.
4. RAW_CAPTURE/source bytes, prior accepted authority contracts, revision identity and workspace/provenance boundaries remain intact.
5. No unreviewed model/runtime/dependency, private data, generated unsafe output, UI-owned domain truth, native/physical claim or later-child/later-milestone scope is included.
6. Required focused/full/static/security/scope/remote checks and the child log are complete and truthful; the log ends exactly with READY_FOR_INDEPENDENT_AUDIT.

Audit must independently inspect the actual GitHub diff/source and evidence. Builder validation is not acceptance. A failed or blocked child stops the M08-C001 frontier.
