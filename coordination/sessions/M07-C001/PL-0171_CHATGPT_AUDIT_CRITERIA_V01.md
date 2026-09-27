# PL-0171 - ChatGPT Audit Criteria V01

Task: **Detect failed/fragmented sparse models and produce actionable diagnostics**

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CHATGPT_AUDIT_V02.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0171_CODEX_PROMPT_V01.md

All criteria below are mandatory.

1. Root `TASKS.md` authorizes M07-C001 / `READY` / `CODEX` for PL-0171 before
   material work; PL-0170 remains `AUDITED_PASS`, PL-0068 remains
   `OWNER_REQUIRED`, and PL-0172+ remains unauthorized.
2. The implementation is a bounded PackLab-owned diagnostic boundary over the
   accepted PL-0170 `SparseMappingRun` contract, with no change to immutable
   PackScan authority, backend neutrality, provenance, or the COLMAP 3.12.6
   adapter.
3. Diagnostic policy/configuration is immutable, explicitly configured,
   validated, deterministic, and does not smuggle engine-specific CLI flags or
   hidden discovery behavior into the domain boundary.
4. Failed, cancelled, successful-but-empty, and successful-but-fragmented
   outcomes are classified deterministically with stable codes, severity,
   actionable message/remediation, and truthful observed statistics.
5. Registration threshold semantics are documented and behaviorally correct at
   zero, exact-threshold, just-below-threshold, and all-registered boundaries.
6. Missing/invalid statistics or invalid PL-0170 result invariants fail closed;
   failed/cancelled runs cannot be reported healthy and an asset identity cannot
   be treated as proof of filesystem materialization or sparse-model health.
7. Reports are portable and safe: no private absolute paths, credentials,
   unredacted stdout/stderr, machine-specific engine discovery, or identity
   timestamps are emitted; machine-readable serialization is stable.
8. Public-boundary tests cover valid complete registration, zero registration,
   threshold boundaries, fragmented registration, failed/cancelled runs,
   missing/invalid result data, deterministic serialization, redaction, and
   non-mutation, plus regression against the accepted sparse/reconstruction/
   process/engine/feature/matcher contracts.
9. The exact locked full suite exits 0; warnings, skips, unavailable external
   engines, and native/physical limitations are reported truthfully.
10. Ruff, targeted mypy, compileall, `git diff --check`, protected-file/scope,
    dependency/lock, privacy/secrets/signing, generated, and binary reviews
    pass truthfully; unchanged repository-wide mypy debt is disclosed.
11. The matching `PL-0171_CODEX_LOG_V01.md` exists, uses full GitHub URLs,
    records exact commands/results/SHAs/limitations and separate publication
    boundaries, and ends exactly `AWAITING_AUDIT`.
12. No PL-0172 export, PL-0173 preset orchestration, OpenMVS/dense stage,
    feature/matcher change, image/pixel processing, camera solving,
    segmentation, UI workflow, neural/generative model, metric calibration,
    schema/dependency/lock, physical/native-device acceptance, tracker edit,
    ChatGPT audit artifact edit, or PL-0172+ implementation is included.

Closure requires a fresh independent ChatGPT audit of the PL-0171
implementation diff, source, tests, and handoff against every criterion.
