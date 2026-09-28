# PL-0177 - ChatGPT Audit Criteria V01

Task: **Implement the OpenMVS mesh-refinement stage**

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0176_CHATGPT_AUDIT_V02.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0177_CODEX_PROMPT_V01.md

All criteria below are mandatory for closure of PL-0177 V01.

1. Root `TASKS.md` authorizes PL-0177 V01 with status `READY` and Required
   Actor `CODEX`; PL-0176 remains `AUDITED_PASS`, PL-0068 remains
   `OWNER_REQUIRED`, and PL-0178+ remains unauthorized.
2. The diff is limited to the new mesh-refinement adapter, its public tests,
   and the matching V01 log. Accepted PL-0176 and predecessor behavior,
   tracker state, audit artifacts, schemas, dependencies, locks, and protected
   files are preserved.
3. The refinement request requires a successful predecessor mesh run, a
   distinct safe output identity, immutable provenance, `RECONSTRUCTION_OBSERVATION`
   authority, and preservation of the predecessor scale state without claiming
   `METRIC_VERIFIED`.
4. Configuration validation matches the pinned OpenMVS v2.4.0 domains:
   `decimate` is finite and in `(0,1]`; `target_face_num`, `close_holes`, and
   `smooth` are non-negative integers excluding booleans;
   `remove_spurious` and `edge_length` are finite and non-negative;
   `remove_spikes` and `crop_to_roi` are strict booleans; and `roi_border` is
   finite with its positive/negative semantics preserved. Unknown options and
   unsafe/colliding asset IDs fail through PackLab-owned errors.
5. The public command mapping uses the exact pinned `ReconstructMesh`
   refinement spellings and frozen order for `--mesh-file`, `--output-file`,
   and the clean/refinement options. No arbitrary argv, hidden mesh-export,
   export-type, texture, discovery, or installation path is accepted.
6. Execution requires an explicit matching valid `openmvs.ReconstructMesh`
   probe at `2.4.0` and preserves the existing shell-free bounded/redacted
   stage seam, timeout/cancellation propagation, and no-engine-installation
   boundary.
7. Result normalization validates stage identity, status, runtime-boolean
   cancellation, exit-code, duration, output text, and status coherence.
   Only coherent success exposes the configured refined output; failure,
   cancellation, and malformed results expose no output and retain provenance,
   authority, and scale invariants.
8. Public tests are behavior-sensitive through the configuration, request,
   command, execution, normalization, and direct-result boundaries. They cover
   invalid and valid domain edges, unsafe/colliding identities, malformed
   status/cancellation cases, output suppression, timeout/cancellation
   propagation, and predecessor regressions.
9. The exact locked full suite exits `0`; no new skip/xfail hides a finding,
   and unavailable `cv2`, symlink privilege, warnings, and absent OpenMVS
   executable are reported truthfully.
10. Ruff, format, targeted mypy, compileall, diff, protected-file/scope,
    dependency/lock, privacy/secrets/signing, generated/binary, and
    remote-visibility checks pass truthfully; unchanged repository-wide mypy
    debt is disclosed.
11. `PL-0177_CODEX_LOG_V01.md` uses full GitHub URLs, records exact commands,
    results, SHAs, limitations, scope, and separate publication boundaries,
    and ends exactly `AWAITING_AUDIT`.
12. No mesh output preservation, parsing/materialization, texturing,
    orchestration, later-stage implementation, schema/dependency/lock change,
    tracker or ChatGPT-audit edit by Codex, generated/private artifact,
    physical/native-device acceptance, or PL-0178+ implementation is included.

Closure requires a fresh independent ChatGPT audit of the V01 diff, source,
tests, and handoff against every criterion.
