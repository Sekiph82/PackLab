# PL-0170 - ChatGPT Audit Criteria V02

Task: **Sparse mapper stage and registered-image statistics remediation**

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CHATGPT_AUDIT_V01.md

Prior implementation:
https://github.com/Sekiph82/PackLab/commit/4225fe4209ae30bdc3f05d4c77612b5ad13609ee

All criteria below are mandatory.

1. Root `TASKS.md` authorizes M07-C001 / `CHANGES_REQUIRED` / `CODEX` for the
   PL-0170 V02 remediation before material work; PL-0169 remains accepted,
   PL-0068 remains `OWNER_REQUIRED`, and PL-0171+ remains unauthorized.
2. The V01 accepted request/configuration behavior, OpenReality architecture,
   PL-0163 contract, immutable PackScan authority, prior feature/matcher
   boundaries, and M07 COLMAP 3.12.6 baseline remain intact except for the
   bounded result-boundary correction.
3. Overflowed, invalid, non-finite, or otherwise unrepresentable ratio values
   fail through the PackLab-owned `SparseMappingSummaryError` boundary; no raw
   `OverflowError`, `ValueError`, or equivalent conversion exception escapes.
4. A normalized stage result must have the exact `sparse-mapping` stage ID and
   internally consistent status, `cancelled` flag, and success exit-code
   semantics. Wrong-stage and contradictory results fail closed and cannot
   expose sparse output.
5. A successful machine-readable summary contains exactly one valid
   repository-relative sparse-output identity. The canonical field and
   supported alias may both appear only when equal; missing, null, conflicting,
   unsafe, mismatched, and ambiguous identities fail closed. The output path is
   an identity/contract, not a claim of external filesystem materialization.
6. `SparseMappingRun` itself enforces successful-result invariants, including
   exact request-image-count/statistics binding, valid stage identity/status,
   and expected output identity. Failed/cancelled results expose neither
   statistics nor sparse output.
7. The original V01 request/configuration boundary remains immutable,
   backend-neutral, deterministically serialized/digested, bound to exact
   input order/source revision and digest/matcher identity/engine version, and
   free of private absolute paths.
8. The explicit COLMAP adapter remains version-checked and command-bound,
   executes only an explicitly supplied matching already-probed executable
   through the existing bounded process seam, and adds no discovery,
   installation, download, fallback, or unrelated engine execution.
9. Focused behavior-sensitive tests cover the V01 behavior plus huge numeric
   ratios, wrong stage IDs, contradictory cancellation flags, inconsistent
   success exits, missing/null/conflicting output identities, direct-result
   invariants, failure/cancellation output suppression, redaction, and
   regression against reconstruction/process/engine and feature/matcher
   contracts.
10. The exact locked full suite exits 0; warnings, skips, unavailable external
    engines, and native/physical limitations are reported truthfully.
11. Ruff, targeted mypy, compileall, `git diff --check`, protected-file/scope,
    dependency/lock, privacy/secrets/signing, generated, and binary reviews
    pass truthfully; unchanged repository-wide mypy debt is disclosed.
12. The matching `PL-0170_CODEX_LOG_V02.md` exists, uses full GitHub URLs,
    records exact commands/results/SHAs/limitations and separate publication
    boundaries, and ends exactly `AWAITING_AUDIT`.
13. No PL-0171 diagnosis, PL-0172 export, PL-0173 preset orchestration,
    OpenMVS/dense stage, feature/matcher change, image/pixel processing,
    camera solving, segmentation, UI workflow, neural/generative model,
    metric calibration, schema/dependency/lock change, physical/native-device
    acceptance, PL-0171+ implementation, `TASKS.md` edit, or ChatGPT audit
    artifact edit is included.

Closure requires a fresh independent ChatGPT audit of the V02 implementation
diff, source, tests, and handoff against every criterion.
