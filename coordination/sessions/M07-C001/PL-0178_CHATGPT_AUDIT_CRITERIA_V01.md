# PL-0178 - ChatGPT Audit Criteria V01

Task: **Implement the OpenMVS texture stage**

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0177_CHATGPT_AUDIT_V01.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0178_CODEX_PROMPT_V01.md

All criteria below are mandatory for closure of PL-0178 V01.

1. Root `TASKS.md` authorizes PL-0178 V01 with status `READY` and Required
   Actor `CODEX`; PL-0177 remains `AUDITED_PASS`, PL-0068 remains
   `OWNER_REQUIRED`, and PL-0179+ remains unauthorized.
2. The diff is limited to the new texture-stage adapter, its public tests, and
   the matching V01 log. Accepted PL-0177 and predecessor behavior, tracker
   state, audit artifacts, schemas, dependencies, locks, and protected files
   are preserved.
3. The texture request requires a successful predecessor refinement run and
   valid non-null scene/refined-mesh identities, uses a distinct safe output
   identity, preserves immutable predecessor provenance/authority/scale, and
   never claims `METRIC_VERIFIED`.
4. Configuration validation matches the frozen pinned TextureMesh domains:
   safe output identity; the four allowed export types; finite `[0,1]`
   decimation; non-negative integer fields excluding booleans; finite
   non-negative float fields; `[0,1]` cost/smoothness ratio; strict booleans;
   `[0,100]` packing heuristic; uint32 empty color; the `-2`/`-1`/non-negative
   ignore-mask label domain; and non-negative maximum texture size. Unknown
   options and unsafe/colliding asset IDs fail through PackLab-owned errors.
5. The public command mapping uses the exact pinned `TextureMesh` spellings and
   frozen order for input, mesh, output, export type, and semantic texture
   options. No arbitrary argv, view-file, orthographic, CUDA, archive,
   process, verbosity, discovery, installation, or output-preservation path is
   accepted.
6. Execution requires an explicit matching valid `openmvs.TextureMesh` probe at
   `2.4.0` and preserves the existing shell-free bounded/redacted stage seam,
   timeout/cancellation propagation, and no-engine-installation boundary.
7. Result normalization validates stage identity, status, runtime-boolean
   cancellation, exit-code, duration, output text, and status coherence.
   Only coherent success exposes the configured textured output; failure,
   cancellation, and malformed results expose no output and retain provenance,
   authority, and scale invariants.
8. Public tests are behavior-sensitive through configuration, request,
   command, execution, normalization, and direct-result boundaries. They cover
   invalid and valid domain edges, unsafe/colliding identities, malformed
   status/cancellation cases, output suppression, timeout/cancellation
   propagation, probe rejection, and predecessor regressions.
9. The exact locked full suite exits `0`; no new skip/xfail hides a finding, and
   unavailable `cv2`, symlink privilege, warnings, and absent OpenMVS
   executable are reported truthfully.
10. Ruff, format, targeted mypy, compileall, diff, protected-file/scope,
    dependency/lock, privacy/secrets/signing, generated/binary, and
    remote-visibility checks pass truthfully; unchanged repository-wide mypy
    debt is disclosed.
11. `PL-0178_CODEX_LOG_V01.md` uses full GitHub URLs, records exact commands,
    results, SHAs, limitations, scope, and separate publication boundaries,
    and ends exactly `AWAITING_AUDIT`.
12. No mesh/texture output preservation or parsing, quality/coverage claims,
    orchestration, PL-0179 output retention, CPU/GPU preset work, schema/
    dependency/lock change, tracker or ChatGPT-audit edit by Codex,
    generated/private artifact, physical/native-device acceptance, or PL-0179+
    implementation is included.

Closure requires a fresh independent ChatGPT audit of the V01 diff, source,
tests, and handoff against every criterion.
