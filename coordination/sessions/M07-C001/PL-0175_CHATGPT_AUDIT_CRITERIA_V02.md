# PL-0175 - ChatGPT Audit Criteria V02

Task: **Remediate the OpenMVS dense point-cloud semantic option boundary**

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CHATGPT_AUDIT_V01.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CODEX_PROMPT_V02.md

All criteria below are mandatory for closure of PL-0175 V02.

1. Root `TASKS.md` authorizes PL-0175 V02 with status `CHANGES_REQUIRED` and
   Required Actor `CODEX`; PL-0174 remains `AUDITED_PASS`, PL-0068 remains
   `OWNER_REQUIRED`, and PL-0176+ remains unauthorized.
2. The V02 implementation remains limited to the dense-stage configuration
   validator, its public tests, and the matching V02 log; V01 evidence and
   accepted predecessor behavior are preserved.
3. `estimate_colors`, `estimate_normals`, and `fusion_filter` reject every
   integer outside the pinned OpenMVS v2.4.0 documented domain `0..2` through
   the public configuration boundary.
4. `postprocess_dmaps` accepts supported combinations of flags `1`, `2`, and
   `4`, including `0`, and rejects every value with unsupported bits.
5. Valid V01 defaults and complete argv mapping remain unchanged; invalid
   semantic values are rejected before command construction/execution.
6. The prior V01 request/result provenance, authority/scale, probe matching,
   shell-free stage execution, timeout/cancellation propagation, failure and
   cancellation output suppression, and predecessor conversion contracts
   remain intact.
7. Public tests are behavior-sensitive: removing each new domain check makes
   at least one invalid case fail, while valid edge and composite values pass.
8. The exact locked full suite exits 0; no new skip/xfail hides the finding,
   and unavailable `cv2`, symlink privilege, warnings, and absent OpenMVS
   executable are reported truthfully.
9. Ruff, format, targeted mypy, compileall, diff, protected-file/scope,
   dependency/lock, privacy/secrets/signing, generated/binary, and
   remote-visibility checks pass truthfully; unchanged repository-wide mypy
   debt is disclosed.
10. `PL-0175_CODEX_LOG_V02.md` uses full GitHub URLs, records exact commands,
    results, SHAs, remediation chronology, and publication boundaries, and
    ends exactly `AWAITING_AUDIT`.
11. No mesh/refinement/texture stage, output preservation, orchestration,
    discovery/installation, schema/dependency/lock change, tracker or
    ChatGPT-audit edit by Codex, physical/native-device acceptance, or
    PL-0176+ implementation is included.

Closure still requires a fresh independent ChatGPT audit of the V02 diff,
source, tests, and handoff against every criterion.
