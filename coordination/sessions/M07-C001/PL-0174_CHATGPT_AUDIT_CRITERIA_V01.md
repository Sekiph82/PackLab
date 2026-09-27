# PL-0174 - ChatGPT Audit Criteria V01

Task: **Implement COLMAP-to-OpenMVS scene conversion**

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0173_CHATGPT_AUDIT_V01.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CODEX_PROMPT_V01.md

All criteria below are mandatory.

1. Root `TASKS.md` authorizes M07-C001 / `READY` / `CODEX` for PL-0174 before
   material work; PL-0173 remains `AUDITED_PASS`, PL-0068 remains
   `OWNER_REQUIRED`, and PL-0175+ remains unauthorized.
2. The implementation is limited to a PackLab-owned, backend-neutral,
   deterministic conversion boundary over the accepted `SparseExportBundle`;
   accepted PL-0166 through PL-0173 behavior is not rewritten.
3. The public conversion boundary accepts only the explicit four-artifact
   sparse-export bundle and validates its debug manifest, artifact names,
   provenance identities, engine identity, record counts, and limitations
   without using filesystem state, stdout/stderr guessing, or external tools.
4. The returned typed conversion plan is immutable, versioned, explicitly
   pinned to the accepted OpenMVS `2.4.0` baseline, carries source/revision/
   request/output identity, input artifact identity/digests, camera convention,
   record counts, and a safe PackLab-relative output scene asset ID.
5. Canonical UTF-8-safe serialization contains the complete plan provenance and
   produces a deterministic SHA-256 digest; equivalent mapping insertion orders
   produce identical serialization and digest.
6. Invalid or unsafe bundles fail closed for missing/duplicate artifacts,
   malformed or contradictory manifests, mismatched counts/digests/identities,
   unsafe or absolute/private paths, control characters, non-finite metadata,
   unsupported OpenMVS versions, and caller-controlled OpenMVS/CLI options.
7. The public plan contains PackLab semantic fields only. Any later executable
   mapping is isolated to an adapter helper, does not execute or discover an
   engine, and never serializes a private executable path.
8. The conversion boundary preserves source evidence, relative reconstruction,
   metric verification, and later dense/mesh/texture authority boundaries; it
   makes no claim of `.mvs` filesystem materialization, dense reconstruction,
   mesh, texture, CAD, Scan Master, or `METRIC_VERIFIED` output.
9. Public-boundary tests cover valid conversion, immutable/non-mutating input,
   manifest and artifact integrity, provenance/count mismatches, unsafe paths
   and options, unsupported engine versions, deterministic serialization and
   digest, output limitations, and regression against accepted sparse-export,
   sparse-mapping, reconstruction/process, engine, capability, feature,
   matcher, and preset contracts.
10. The exact locked full suite exits 0; skips, warnings, unavailable external
    engines, aggregate-test limitations, and native/physical limitations are
    reported truthfully without skips or xfails hiding the task.
11. Ruff, format, targeted mypy, compileall, `git diff --check`, protected-file/
    scope, dependency/lock, privacy/secrets/signing, generated, binary, and
    remote-visibility checks pass truthfully; unchanged repository-wide mypy
    debt is disclosed.
12. The matching `PL-0174_CODEX_LOG_V01.md` exists, uses full GitHub URLs,
    records exact commands/results/SHAs/limitations and separate publication
    boundaries, and ends exactly `AWAITING_AUDIT`.
13. No OpenMVS/external-engine execution or discovery, `.mvs` binary writer,
    dense or later stage, orchestration, feature/matcher/image/camera/UI/
    segmentation/neural/metric work, schema/dependency/lock change, tracker or
    ChatGPT audit artifact edit by Codex, physical/native-device acceptance,
    or PL-0175+ implementation is included.

Closure requires a fresh independent ChatGPT audit of the PL-0174
implementation diff, source, tests, and handoff against every criterion.
