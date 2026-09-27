# PL-0168 — ChatGPT Audit Criteria V01

Task: **Feature-extraction configuration optimized first for packaged consumer goods**

Mandatory architecture:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

Mandatory pre-read:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0163_RECONSTRUCTION_BACKEND_CONTRACT.md

Previous child audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CHATGPT_AUDIT_V02.md

All criteria below are mandatory.

1. Root `TASKS.md` authorized M07-C001 / `READY` / `CODEX` for PL-0168 before material work; PL-0158 through PL-0167 remain accepted, PL-0068 remains `OWNER_REQUIRED`, and PL-0169+ remains unauthorized.
2. The implementation is a PackLab-owned, immutable, backend-neutral feature-extraction configuration boundary and does not relocate authority into UI, project tracking, PackScan schemas, RAW_CAPTURE, or camera-prior objects.
3. The initial packaged-consumer-goods preset has deterministic named defaults for image-size limit, feature-count limit, scale-space/octave settings, contrast/peak threshold, edge threshold, and orientation policy; the values and intended tradeoffs are explicit and are not represented as physical benchmark results.
4. Validated overrides preserve the preset contract, reject unknown/unsafe/non-finite/out-of-range values and absolute paths, and do not mutate source configuration or preset objects.
5. Serialization and configuration digest are deterministic, canonical, stable across equivalent mapping order, and suitable for reconstruction provenance.
6. The COLMAP 3.12.6 mapping uses the correct adapter-bound parameter names/values, is explicit about unsupported options, and does not execute or install an external engine.
7. Focused boundary tests prove defaults/preset identity, valid overrides, digest stability/order independence, invalid values, unsupported options, adapter mapping, non-mutation, and absence of private paths. Relevant accepted reconstruction/engine configuration boundaries remain green.
8. The exact locked full suite exits 0; warnings and environment skips are reported truthfully.
9. Ruff, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/lock, privacy/secrets/signing, and generated/binary reviews pass truthfully; unchanged repository-wide mypy debt is disclosed.
10. The matching `PL-0168_CODEX_LOG_V01.md` exists, uses full GitHub URLs, records exact commands/results/SHAs/limitations and separate publication boundaries, and ends exactly `READY_FOR_INDEPENDENT_AUDIT`.
11. No feature-extraction execution, image processing, matching, sparse/dense reconstruction, camera solving, segmentation, mask lifting, UI workflow, engine installation/execution, neural/generative model, metric calibration, schema/dependency/lock change, physical/native-device acceptance, PL-0169+ implementation, `TASKS.md` edit, or ChatGPT audit artifact edit is included.

Closure requires a fresh independent ChatGPT audit of the actual implementation diff, source, tests, and handoff against every criterion.
