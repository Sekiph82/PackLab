# PL-0181 - ChatGPT Audit Criteria V01

Task: **Add one-click Reconstruct Scan orchestration across COLMAP and OpenMVS**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0181_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. The batch was authorized by the live tracker before implementation and the
   child scope is exactly PL-0181.
2. One public PackLab-owned orchestration boundary composes the existing
   COLMAP/OpenMVS stage contracts in deterministic order and does not duplicate
   engine-specific command ownership.
3. Inputs, preset/resource configuration, workspace/revision, backend
   provenance, stage results, output identities, scale state, authority class,
   and digests remain explicit and traceable.
4. Missing capability, invalid stage dependency, failed/cancelled stage, and
   missing output stop downstream work and produce a coherent fail-closed
   result; partial success is not reported as a complete reconstruction.
5. RAW_CAPTURE/source bytes, accepted workspace isolation, PL-0179 evidence
   retention, and prior stage contracts remain intact.
6. No automatic engine install/download, neural runtime, UI-owned pipeline,
   M08 behavior, metric/CAD/Scan Master claim, or unauthorized scope is added.
7. Public tests cover ordered success, each prerequisite/failure boundary,
   stage stop behavior, provenance/output identity, and predecessor regressions.
8. Required focused/full/static/security/scope checks and child log evidence
   are complete, truthful, and remotely visible; the log ends exactly
   `READY_FOR_INDEPENDENT_AUDIT`.
