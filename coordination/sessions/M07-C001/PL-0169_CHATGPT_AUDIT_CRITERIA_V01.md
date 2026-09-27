# PL-0169 - ChatGPT Audit Criteria V01

Task: **Matcher selection for ordered orbit datasets**

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CHATGPT_AUDIT_V02.md

All criteria below are mandatory.

1. Root `TASKS.md` authorized M07-C001 / `READY` / `CODEX` for PL-0169 before
   material work; PL-0158 through PL-0168 remain accepted, PL-0068 remains
   `OWNER_REQUIRED`, and PL-0170+ remains unauthorized.
2. The implementation preserves the accepted OpenReality architecture,
   PL-0163 backend contract, M07 engine baseline, immutable PackScan source
   authority, the feature-extraction boundary, and the guided-orbit versus
   turntable distinction.
3. The public matcher-selection boundary accepts ordered guided-orbit image
   asset IDs, preserves their exact order, selects a documented sequential
   strategy, and validates an explicit overlap/window policy deterministically.
4. Empty, duplicate, absolute, traversal, malformed, or otherwise unsafe
   asset IDs; unsupported modes; and invalid overlap/configuration values fail
   closed with PackLab-owned diagnostics. Inputs are not mutated.
5. Turntable input is not silently treated as a static-world ordered orbit.
   It is rejected or routed only through an explicitly object-transform-aware
   adapter, with no implicit reinterpretation.
6. Any serialized selection/configuration is canonical and digest-stable
   across equivalent mapping order, and contains no private absolute paths or
   caller-controlled unsafe provenance.
7. Any COLMAP mapping is explicit, adapter-bound, version-checked, and
   configuration-only; no external engine discovery, installation, launch, or
   execution is introduced.
8. Focused tests are behavior-sensitive and cover valid input, exact order,
   overlap boundaries, invalid/unsafe/duplicate input, mode separation,
   deterministic serialization/digest, non-mutation, and regression against
   the reconstruction contract and engine boundaries.
9. The exact locked full suite exits 0; warnings and environment skips are
   reported truthfully.
10. Ruff, targeted mypy, compileall, `git diff --check`, protected-file/scope,
    dependency/lock, privacy/secrets/signing, and generated/binary reviews
    pass truthfully; unchanged repository-wide mypy debt is disclosed.
11. The matching `PL-0169_CODEX_LOG_V01.md` exists, uses full GitHub URLs,
    records exact commands/results/SHAs/limitations and separate publication
    boundaries, and ends exactly `READY_FOR_INDEPENDENT_AUDIT`.
12. No feature matching, image processing, pair computation against pixels,
    sparse/dense reconstruction, camera solving, segmentation, mask lifting,
    UI workflow, engine installation/execution, neural/generative model,
    metric calibration, schema/dependency/lock change, physical/native-device
    acceptance, PL-0170+ implementation, `TASKS.md` edit, or ChatGPT audit
    artifact edit is included.

Closure requires a fresh independent ChatGPT audit of the PL-0169
implementation diff, source, tests, and handoff against every criterion.
