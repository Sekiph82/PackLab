# PL-0176 - ChatGPT Audit Criteria V02

Task: **OpenMVS mesh-reconstruction stage fail-closed remediation**

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0176_CHATGPT_AUDIT_V01.md

Prior implementation:
https://github.com/Sekiph82/PackLab/commit/0513967739060067b495b2f46320990ebc3b301d

All criteria below are mandatory for closure of PL-0176 V02.

1. Root `TASKS.md` authorizes M07-C001 / `CHANGES_REQUIRED` / `CODEX` for
   PL-0176 V02 before material work; PL-0175 remains `AUDITED_PASS`, PL-0068
   remains `OWNER_REQUIRED`, and PL-0177+ remains unauthorized.
2. The V01 accepted mesh request/configuration, pinned OpenMVS command/probe
   mapping, provenance, authority, scale, process, and predecessor behavior
   remain intact except for the two bounded fail-closed corrections.
3. Huge, unrepresentable, non-finite, negative, boolean-as-number, and other
   invalid numeric mesh configuration values fail through the PackLab-owned
   `InvalidMeshReconstructionRequest` boundary; no raw `OverflowError` or
   equivalent conversion exception escapes.
4. The stage-result boundary requires `cancelled` to be a runtime boolean and
   requires coherent stage identity, status, cancellation, exit-code, and
   duration semantics. Non-boolean values fail closed before a valid result is
   reported.
5. Successful, failed, and cancelled normalized/direct mesh results preserve
   the V01 output-identity, provenance, authority, and scale invariants;
   malformed cancellation values never expose a mesh output or claim a valid
   cancellation.
6. Public tests are behavior-sensitive and cover both V01 findings through
   `MeshReconstructionConfig.from_overrides`, normalization, and direct
   `MeshReconstructionRun` construction, including huge numeric inputs,
   falsey/truthy non-boolean cancellation values, valid defaults/edges, and
   failure/cancellation output suppression.
7. The explicit `openmvs.ReconstructMesh` probe/version/executable matching,
   exact pinned argv, shell-free bounded/redacted process seam,
   timeout/cancellation propagation, and no-discovery/no-installation boundary
   remain unchanged.
8. The exact locked full suite exits 0; no new skip/xfail hides a finding, and
   unavailable `cv2`, symlink privilege, warnings, and absent OpenMVS executable
   are reported truthfully.
9. Ruff, format, targeted mypy, compileall, diff, protected-file/scope,
   dependency/lock, privacy/secrets/signing, generated/binary, and
   remote-visibility checks pass truthfully; unchanged repository-wide mypy
   debt is disclosed.
10. `PL-0176_CODEX_LOG_V02.md` uses full GitHub URLs, records exact commands,
    results, SHAs, limitations, correction chronology, and publication
    boundaries, and ends exactly `AWAITING_AUDIT`.
11. The V02 diff remains limited to the mesh adapter, its public tests, and
    the matching V02 log; no tracker/audit edit by Codex, accepted-predecessor
    change, schema/dependency/lock change, generated/binary/private artifact,
    physical/native-device acceptance, or PL-0177+ implementation is included.

Closure requires a fresh independent ChatGPT audit of the V02 diff, source,
tests, and handoff against every criterion.
