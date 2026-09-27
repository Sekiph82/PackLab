# PL-0168 - ChatGPT Audit Criteria V02

Task: **Feature-extraction configuration optimized first for packaged consumer goods remediation**

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CHATGPT_AUDIT_V01.md

Prior implementation:
https://github.com/Sekiph82/PackLab/commit/2cfdfab7dd15f8b21e472d0296f18c7ab40ed53e

All criteria below are mandatory.

1. Root `TASKS.md` authorizes M07-C001 / `CHANGES_REQUIRED` / `CODEX` for the
   PL-0168 V02 remediation before material work; PL-0158 through PL-0167
   remain accepted, PL-0068 remains `OWNER_REQUIRED`, and PL-0169+ remains
   unauthorized.
2. The V01 accepted behavior, OpenReality architecture, PL-0163 contract,
   engine baseline, immutable preset identity/defaults, backend-neutral fields,
   and COLMAP adapter boundary remain intact except for the bounded correction.
3. Supported override mappings are normalized deterministically: equal mappings
   with the same key/value pairs produce the same normalized values,
   serialization, and digest regardless of insertion order. Conflicting alias
   or canonical-plus-alias values do not silently overwrite one another and are
   rejected or resolved by an explicit order-independent rule.
4. Valid single-field overrides remain non-mutating and continue to reject
   unknown/unsafe/non-finite/out-of-range values, unsupported backend options,
   and absolute paths.
5. Canonical serialization and configuration digest remain deterministic,
   stable across equivalent mapping order, and suitable for reconstruction
   provenance.
6. The COLMAP 3.12.6 mapping remains explicit and adapter-bound, rejects an
   unsupported engine version, and does not execute or install an external
   engine.
7. Focused tests prove defaults/preset identity, valid overrides, alias-order
   determinism, conflicting-alias rejection or deterministic resolution,
   digest stability, invalid/non-finite/out-of-range values, unsupported
   options, adapter mapping, non-mutation, and absence of private paths.
8. The exact locked full suite exits 0; warnings and environment skips are
   reported truthfully.
9. Ruff, targeted mypy, compileall, `git diff --check`, protected-file/scope,
   dependency/lock, privacy/secrets/signing, and generated/binary reviews pass
   truthfully; unchanged repository-wide mypy debt is disclosed.
10. The matching `PL-0168_CODEX_LOG_V02.md` exists, uses full GitHub URLs,
    records exact commands/results/SHAs/limitations and separate publication
    boundaries, and ends exactly `READY_FOR_INDEPENDENT_AUDIT`.
11. No feature-extraction execution, image processing, matching, sparse/dense
    reconstruction, camera solving, segmentation, mask lifting, UI workflow,
    engine installation/execution, neural/generative model, metric
    calibration, schema/dependency/lock change, physical/native-device
    acceptance, PL-0169+ implementation, `TASKS.md` edit, or ChatGPT audit
    artifact edit is included.

Closure requires a fresh independent ChatGPT audit of the V02 implementation
diff, source, tests, and handoff against every criterion.
