# PL-0186 — ChatGPT Audit Criteria V02

Task: **Implement the owner-approved SAM 2.1 Hiera Base+ local PyTorch segmentation backend**

Owner decision:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0004-sam2.1-segmentation-backend.md

Mandatory contract pre-read:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CODEX_PROMPT_V02.md

All criteria are mandatory.

1. The live tracker authorized M08-C001 / PL-0186 V02 / READY / CODEX before implementation; M07 remains closed, PL-0184/PL-0185 remain independently accepted, PL-0068 remains OWNER_REQUIRED, and PL-0187+ / M09 remain unauthorized.
2. The implementation reads and preserves ADR-0004 and the PL-0184 backend contract. SAM-specific APIs remain inside the backend/runtime adapter boundary and no downstream mask/geometry consumer imports SAM-specific code.
3. Frozen model identity is exactly:
   - upstream repository: https://github.com/facebookresearch/sam2
   - reviewed source revision: `2b90b9f5ceec907a1c18123530e92e794ad901a4`
   - model: SAM 2.1 Hiera Base+
   - checkpoint: `sam2.1_hiera_base_plus.pt`
   - config: `configs/sam2.1/sam2.1_hiera_b+.yaml`
   - repository source license: Apache-2.0.
4. Checkpoint acquisition/provenance is explicit and fail-closed:
   - only the official source approved by ADR-0004 is accepted;
   - no silent/application-time auto-download exists;
   - checkpoint binary is not committed to Git;
   - local byte size and SHA-256 are recorded in evidence/provenance;
   - configured checkpoint missing/hash mismatch causes capability unavailable or execution failure, never fabricated success.
5. Runtime is local PyTorch only. No hosted API, credential, remote inference service or hidden network dependency is introduced.
6. Exact runtime facts are recorded: Python, PyTorch, torchvision, SAM 2 revision/package form, device, CUDA availability/version when applicable, and whether native Windows or WSL is actually used. Runtime capability is probed rather than assumed.
7. CUDA is optional. A validated CUDA path may be used when available. CPU fallback remains a supported functional path or a truthfully reported bounded limitation, but no CPU performance guarantee is claimed.
8. Public backend behavior is deterministic/provenance-bound and preserves PL-0184 coordinate/authority rules:
   - source image ID/digest;
   - source dimensions and top-left source pixel convention;
   - resize/transform metadata;
   - model/checkpoint identity and SHA-256;
   - runtime/device provenance;
   - prompt provenance;
   - immutable RAW_CAPTURE.
9. Supported prompt/capability behavior is proven through the public boundary. At minimum point and box prompt support must be implemented or truthfully reported unavailable. Automatic mask generation may be exposed only if implemented and capability-probed.
10. Model input/output normalization is bounded and fail-closed. Malformed output, dimension mismatch, non-finite/invalid confidence, missing runtime, missing model/config/checkpoint and unsupported prompt modes do not produce valid masks.
11. No PL-0187 post-processing implementation is smuggled into PL-0186. SAM 2 internal/model output handling may be normalized as required, but PackLab hole filling, edge cleanup and small-component-removal policy remains PL-0187.
12. Tests include:
    - backend replacement remains transparent to downstream consumers;
    - capability available/unavailable;
    - exact model/config/checkpoint provenance;
    - checkpoint hash success and mismatch rejection;
    - no auto-download/network path;
    - point prompt;
    - box prompt;
    - source-pixel transform round trip;
    - malformed/mismatched output rejection;
    - source-byte immutability;
    - CPU/device capability behavior through a fake/local runner boundary;
    - accepted PL-0184/PL-0185 regression behavior.
13. If a real local SAM 2.1 validation run is possible, it is bounded to public/synthetic test imagery and its result is evidence only. No private scans or supplier assets are required.
14. Dependency/lock changes are minimal, reviewed and reproducible. Every added package/build artifact has an explicit license/provenance record. Do not casually inject GPU-specific wheels into the canonical application lock if the architecture uses an external/local ML runtime environment.
15. Focused tests, relevant regressions, exact locked full suite, Ruff/format, targeted mypy, compileall, git diff --check, protected-file/scope, dependency/license, privacy/secrets, generated/binary and remote visibility checks are complete and truthful.
16. Codex does not edit `TASKS.md`, owner decision artifacts or ChatGPT audit/criteria files.
17. Publish a separate implementation/evidence commit and a separate child-log-only commit:
    https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CODEX_LOG_V02.md
18. The child log records exact commands, actual versions, checkpoint source/size/SHA-256, runtime/device result, changed files, tests, limitations and commit SHAs, and ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

A failure or blocker stops the frontier. Do not start PL-0187.
