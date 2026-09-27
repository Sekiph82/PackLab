# PL-0170 - ChatGPT Audit Criteria V01

Task: **Sparse mapper stage and registered-image statistics**

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0169_CHATGPT_AUDIT_V01.md

All criteria below are mandatory.

1. Root `TASKS.md` authorized M07-C001 / `READY` / `CODEX` for PL-0170 before
   material work; PL-0169 remains independently accepted, PL-0068 remains
   `OWNER_REQUIRED`, and PL-0171+ remains unauthorized.
2. The implementation preserves the accepted OpenReality architecture,
   PL-0163 backend contract, immutable PackScan source authority, prior
   feature-extraction and matcher boundaries, and the M07 COLMAP 3.12.6
   baseline.
3. The sparse-mapper request/configuration is immutable, backend-neutral,
   deterministically serialized, digest-stable, and bound to the exact input
   asset order, source revision/digest, matcher-selection identity, and engine
   version without private absolute paths.
4. Invalid, missing, duplicate, unsafe, absolute, traversal, mismatched, or
   otherwise ambiguous input/provenance values fail closed with PackLab-owned
   diagnostics and do not mutate caller inputs or accepted upstream objects.
5. The COLMAP sparse-mapper adapter is explicit, version-checked, and
   configuration/command-bound. Execution, when present, uses only an
   explicitly supplied already-probed executable through the existing bounded
   process seam; no discovery, installation, download, silent fallback, or
   unrelated engine execution is introduced.
6. Successful, failed, and cancelled stage outcomes map deterministically to
   PackLab reconstruction-stage semantics, retain bounded/redacted evidence,
   preserve immutable RAW_CAPTURE, and never report success without a valid
   stage result/output contract.
7. Registered-image statistics contain at least total, registered,
   unregistered, and a deterministic count/ratio relationship; malformed,
   inconsistent, overflowed, or ambiguous summaries fail closed rather than
   being guessed from pixels or arbitrary human log text.
8. Focused behavior-sensitive tests cover valid binding/order, command
   mapping, statistics boundaries and malformed input, version rejection,
   process failure/cancellation, non-mutation, redaction, serialization/digest
   determinism, and regression against reconstruction/process/engine and the
   accepted feature/matcher contracts.
9. The exact locked full suite exits 0; warnings, skips, unavailable external
   engines, and any native/physical limitations are reported truthfully.
10. Ruff, targeted mypy, compileall, `git diff --check`, protected-file/scope,
    dependency/lock, privacy/secrets/signing, generated, and binary reviews
    pass truthfully; unchanged repository-wide mypy debt is disclosed.
11. The matching `PL-0170_CODEX_LOG_V01.md` exists, uses full GitHub URLs,
    records exact commands/results/SHAs/limitations and separate publication
    boundaries, and ends exactly `AWAITING_AUDIT`.
12. No PL-0171 diagnosis, PL-0172 export, PL-0173 preset orchestration,
    OpenMVS/dense stage, feature/matcher change, image/pixel processing,
    camera solving, segmentation, UI workflow, neural/generative model,
    metric calibration, schema/dependency/lock change, physical/native-device
    acceptance, PL-0171+ implementation, `TASKS.md` edit, or ChatGPT audit
    artifact edit is included.

Closure requires a fresh independent ChatGPT audit of the PL-0170
implementation diff, source, tests, and handoff against every criterion.
