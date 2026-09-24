# PL-0102 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorized.
2. M03 and PL-0111 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. No TASKS/audit edits; no M05.
4. V01 correct behavior preserved.
5. Previous V01 audit fully addressed.
6. Change orbit coverage input from arbitrary raw PoseSample to authoritative accepted-capture pose evidence (PoseCaptureBinding/AcceptedCaptureRecord.poseBinding or an equivalent production-used typed seam).
7. Only `available` aligned normal-tracking pose evidence may create coverage; stale/unavailable/invalid bindings must remain explicit invalid observations.
8. Wire accepted capture completion into the one OrbitCoverageModel owned by the active guided-capture session.
9. Add tests for azimuth wrap, elevation min/max boundaries, stale/unavailable/invalid bindings, duplicate sector capture and deterministic totals.
10. Tests hit the production-used quality/coverage/capture seam.
11. Validation/git diff/privacy checks are truthful and clean.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
