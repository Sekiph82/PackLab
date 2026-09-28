# PL-0176 - ChatGPT Audit Criteria V01

Task: **Implement the OpenMVS mesh-reconstruction stage**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0176_CODEX_PROMPT_V01.md

Accepted predecessor:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CHATGPT_AUDIT_V02.md

All criteria below are mandatory for closure of PL-0176 V01.

1. Root `TASKS.md` authorizes PL-0176 with status `READY` and Required Actor
   `CODEX`; PL-0175 is `AUDITED_PASS`, PL-0068 is `OWNER_REQUIRED`, and
   PL-0177+ remains unauthorized.
2. The implementation is limited to the mesh-stage adapter, its public tests,
   and the matching V01 log; PL-0175 and accepted predecessor behavior are
   preserved.
3. The public request boundary accepts only a successful, provenance-bound
   dense-stage input with safe relative asset identities, exact source/plan/
   configuration/request identity, and pinned OpenMVS `2.4.0` identity.
4. The semantic configuration validates the documented reconstruction options:
   finite/non-negative `min_point_distance`, `thickness_factor`, and
   `quality_factor`; boolean `integrate_only_roi`, `constant_weight`, and
   `free_space_support`; valid defaults remain accepted; raw or caller-
   controlled CLI options are rejected.
5. The adapter emits the complete, correctly ordered pinned `ReconstructMesh`
   argv for the supported reconstruction options and rejects unsafe input or
   output asset IDs before command construction/execution.
6. Execution requires a matching valid OpenMVS `ReconstructMesh` probe at
   version `2.4.0`, uses the existing shell-free process boundary, propagates
   timeout/cancellation, bounds/redacts output, and performs no discovery,
   installation, or download.
7. Success, failure, cancellation, exit-code, stage-identity, output-identity,
   provenance, authority, and scale invariants are fail-closed; failure or
   cancellation never exposes a successful mesh output, and no mesh quality or
   geometry count is inferred from engine output.
8. Public tests are behavior-sensitive: invalid semantic values, unsafe IDs,
   wrong/missing probes, malformed result states, failure/cancellation output
   suppression, and provenance drift fail through the public boundary, while
   valid edge/default mappings pass.
9. The exact locked full suite exits 0; no new skip/xfail hides a finding, and
   unavailable `cv2`, symlink privilege, warnings, and absent OpenMVS executable
   are reported truthfully.
10. Ruff, format, targeted mypy, compileall, diff, protected-file/scope,
    dependency/lock, privacy/secrets/signing, generated/binary, and
    remote-visibility checks pass truthfully; unchanged repository-wide mypy
    debt is disclosed.
11. `PL-0176_CODEX_LOG_V01.md` uses full GitHub URLs, records exact commands,
    results, SHAs, limitations, and publication boundaries, and ends exactly
    `AWAITING_AUDIT`.
12. No refinement, texturing, output preservation, orchestration, discovery/
    installation, dense-stage modification, schema/dependency/lock change,
    tracker or ChatGPT-audit edit by Codex, physical/native-device acceptance,
    or PL-0177+ implementation is included.

Closure requires a fresh independent ChatGPT audit of the V01 diff, source,
tests, and handoff against every criterion.
