# PL-0167 - ChatGPT Audit Criteria V02

Task: **PackScan camera intrinsics and pose-prior consumption remediation**

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CHATGPT_AUDIT_V01.md

Prior implementation:
https://github.com/Sekiph82/PackLab/commit/12f630461fdadaa7cad8607ace10771b99353b69

All criteria below are mandatory.

1. Root `TASKS.md` authorizes M07-C001 / `CHANGES_REQUIRED` / `CODEX` for the PL-0167 V02 remediation before material work; PL-0158 through PL-0166 remain accepted, PL-0068 remains `OWNER_REQUIRED`, and PL-0168+ remains unauthorized.
2. The V01 accepted behavior, OpenReality architecture, ADR-0003, PL-0163 contract, PackScan authority, and PL-0166 byte-preserving working-set seam remain intact except for the bounded corrections below.
3. Every non-rejected prior accepted by `assess_camera_priors` is bound to the exact `ReconstructionInputSet` source digest and source revision and carries a valid source image identity; missing or mismatched binding fields are explicitly rejected with warnings/reasons.
4. Duplicate PackScan metadata candidates for the same `(kind, photo_id)` are permanently ambiguous: no candidate is selected for that key when two, three, or more uniquely named payloads are present. A valid unique payload remains selectable.
5. The PackScan importer continues to map valid intrinsics and available poses to exact revision-scoped PL-0166 working image IDs, validates schemas/conventions/dimensions/lens/units/source/policy, and preserves explicit ignored, initialization-only, fixed, refined, and rejected semantics without granting metrology authority.
6. Focused production-boundary tests prove the missing-binding rejection and three-or-more duplicate rejection, as well as retaining valid mapping, normalization, malformed/missing metadata, dimension/lens/convention/unit mismatch, all use modes, source/revision mismatch, and RAW_CAPTURE/working-set immutability.
7. No feature extraction, matching, sparse/dense reconstruction, camera solving, segmentation, mask lifting, UI workflow, external engine/model installation or execution, metric calibration, neural/generative model, schema/dependency/lock change, or PL-0168+ implementation is included.
8. Focused tests and `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs` exit 0; warnings and environment skips are reported truthfully.
9. Ruff, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/lock, privacy/secrets/signing, and generated/binary reviews pass truthfully; unchanged repository-wide mypy debt is disclosed.
10. The matching `PL-0167_CODEX_LOG_V02.md` exists, uses full GitHub URLs, records exact commands/results/SHAs/limitations and the separate publication boundary, and ends exactly `READY_FOR_INDEPENDENT_AUDIT`.
11. Codex does not edit `TASKS.md`, create/edit ChatGPT audit artifacts, self-audit, assign `AUDITED_PASS`, overwrite V01 evidence, or start PL-0168.

Closure requires a fresh independent ChatGPT audit of the V02 implementation diff, source, tests, and handoff plus verification that the V01 findings are closed.
