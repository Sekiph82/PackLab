# PL-0167 — ChatGPT Audit Criteria V01

Task: **PackScan camera intrinsics and pose-prior consumption**

Mandatory architecture:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

Architecture decision:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0003-object-centric-reconstruction-authority.md

Mandatory pre-read:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0163_RECONSTRUCTION_BACKEND_CONTRACT.md

Previous child audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0166_CHATGPT_AUDIT_V01.md

Criteria:

1. Root `TASKS.md` authorizes M07-C001 / READY / CODEX for PL-0167 before material work; PL-0158 through PL-0166 remain independently accepted, PL-0068 remains `OWNER_REQUIRED`, and PL-0168+ is not authorized.
2. The OpenReality architecture, ADR-0003, PL-0163 contract, accepted PackScan/project/workspace/provenance authorities, and the PL-0166 byte-preserving working-set seam remain intact.
3. A PackLab-owned seam reads valid PackScan per-image intrinsics and available capture pose observations through the accepted PackScan authority and associates them with exact revision-scoped PL-0166 working image IDs.
4. Intrinsics and poses are validated and normalized under an explicit camera convention, dimensions, lens identity, units, source, and policy/version; ambiguous or inconsistent values are rejected or explicitly marked `REJECTED`, never silently guessed.
5. The implementation supports the existing explicit prior-use semantics—fixed, initialization-only, refined, ignored, and rejected—and does not promote ARKit/CoreMotion or capture metadata to metrology-grade truth or M09 metric authority.
6. Priors are bound to the exact source digest, working-set revision, image IDs, image dimensions/lens identity, and convention; drift or mismatch invalidates/rejects reuse.
7. Focused tests are behavior-sensitive for valid mapping, malformed/missing metadata, dimension/lens/convention/unit mismatch, all prior-use modes, revision/image binding, rejection behavior, and RAW_CAPTURE/working-set immutability.
8. No feature extraction, matching, sparse/dense reconstruction, camera solving, segmentation, mask lifting, UI workflow, external engine/model installation or execution, metric calibration, neural/generative model, or PL-0168+ implementation is included.
9. Focused tests and `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs` exit 0.
10. Ruff, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/lock, privacy/secrets/signing, and generated/binary reviews pass truthfully; unchanged repository-wide mypy debt is disclosed and no changed module adds an error.
11. The child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CODEX_LOG_V01.md, uses full GitHub URLs, records exact commands/results/SHAs/limitations, and ends exactly `READY_FOR_INDEPENDENT_AUDIT`.
12. Codex does not edit `TASKS.md`, create/edit ChatGPT audit artifacts, self-audit, assign `AUDITED_PASS`, or start PL-0168; implementation and log publication boundaries are separately reviewable.

Closure requires a fresh independent ChatGPT audit of the actual GitHub diff, source, tests, and handoff.
