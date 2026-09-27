# PL-0174 - ChatGPT Audit Criteria V02

Task: **Remediate COLMAP artifact record validation in the OpenMVS conversion boundary**

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CHATGPT_AUDIT_V01.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CODEX_PROMPT_V02.md

All criteria below are mandatory for closure of PL-0174.

1. Root `TASKS.md` authorizes M07-C001 / `CHANGES_REQUIRED` / `CODEX` for
   PL-0174 before material work; PL-0173 remains `AUDITED_PASS`, PL-0068
   remains `OWNER_REQUIRED`, and PL-0175+ remains unauthorized.
2. The V02 diff is bounded to the V01 record-integrity correction and its
   evidence; accepted PL-0166 through PL-0173 behavior is not rewritten.
3. The public boundary rejects malformed COLMAP camera records, including
   unsupported models, wrong parameter cardinality, non-positive/non-integer
   dimensions, and non-finite parameters, while preserving the accepted
   camera identity/count checks.
4. The public boundary rejects malformed COLMAP image records, including a
   zero quaternion, unsafe or duplicate image names, invalid pose/camera
   fields, malformed observations, and non-finite coordinates; existing
   camera/point/track consistency remains enforced.
5. The public boundary rejects malformed COLMAP point records, including
   invalid RGB values, invalid point/error values, empty tracks, malformed
   track IDs, and non-finite metadata; existing exact observation/track
   equality remains enforced.
6. V01 accepted behavior remains intact: the explicit four-artifact bundle,
   strict debug manifest, provenance identities, counts, limitations, safe
   output IDs, immutable plan, OpenMVS `2.4.0` pin, canonical serialization/
   digest, no CLI options, and no engine execution/discovery.
7. Public tests cover every V01 finding and the new malformed camera/image/
   point boundaries through the public conversion function, plus the accepted
   sparse-export and regression suites.
8. The exact locked full suite exits 0; skips, warnings, unavailable engines,
   and native/physical limitations are reported truthfully without skips or
   xfails hiding the remediation.
9. Ruff, format, targeted mypy, compileall, `git diff --check`, protected-file/
   scope, dependency/lock, privacy/secrets/signing, generated, binary, and
   remote-visibility checks pass truthfully; unchanged repository-wide mypy
   debt is disclosed.
10. The matching `PL-0174_CODEX_LOG_V02.md` exists, uses full GitHub URLs,
    records exact commands/results/SHAs/limitations and separate publication
    boundaries, and ends exactly `AWAITING_AUDIT`.
11. No OpenMVS/external-engine execution or discovery, `.mvs` writer, dense or
    later stage, orchestration, unrelated image/camera processing, schema/
    dependency/lock change, tracker or ChatGPT audit artifact edit, physical/
    native-device acceptance, or PL-0175+ implementation is included.

Closure requires a fresh independent ChatGPT audit of the V02 implementation
diff, source, tests, and handoff against every criterion.
