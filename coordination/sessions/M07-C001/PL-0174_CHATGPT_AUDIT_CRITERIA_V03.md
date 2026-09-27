# PL-0174 - ChatGPT Audit Criteria V03

Task: **Correct remaining COLMAP artifact contract compatibility at the OpenMVS conversion boundary**

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CHATGPT_AUDIT_V02.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CODEX_PROMPT_V03.md

All criteria below are mandatory for closure of PL-0174.

1. Root `TASKS.md` authorizes M07-C001 / `CHANGES_REQUIRED` / `CODEX` for
   PL-0174 before material work; PL-0173 remains `AUDITED_PASS`, PL-0068
   remains `OWNER_REQUIRED`, and PL-0175+ remains unauthorized.
2. The V03 diff is bounded to the two V02 parser-compatibility findings and
   their evidence; accepted PL-0166 through PL-0173 behavior is not rewritten.
3. The public camera boundary rejects unsupported models, wrong parameter
   cardinality, non-positive/non-integer dimensions, non-finite parameters,
   and non-positive model-specific focal parameters while preserving camera
   identity/count and cross-file checks.
4. The public image boundary rejects zero quaternions, unsafe or duplicate
   names, invalid pose/camera fields, malformed pairs/observations, and
   non-finite coordinates, while accepting a valid exporter image with an
   empty observation line and preserving camera/point/track consistency.
5. The public point boundary rejects invalid RGB values, invalid point/error
   values, empty tracks, malformed track IDs, and non-finite metadata; exact
   observation/track equality remains enforced.
6. V02 accepted behavior remains intact: the explicit four-artifact bundle,
   strict debug manifest, provenance identities, counts, limitations, safe
   output IDs, immutable plan, canonical serialization/digest, COLMAP `3.12.6`
   and OpenMVS `2.4.0` pins, no CLI options, and no engine execution/discovery.
7. Public tests cover both V02 findings through the public conversion function:
   non-positive focal rejection and valid zero-observation acceptance. They
   retain every V02 malformed-record case and the accepted sparse-export and
   regression suites.
8. The exact locked full suite exits 0; skips, warnings, unavailable engines,
   and native/physical limitations are reported truthfully without skips or
   xfails hiding the remediation.
9. Ruff, format, targeted mypy, compileall, `git diff --check`, protected-file/
   scope, dependency/lock, privacy/secrets/signing, generated, binary, and
   remote-visibility checks pass truthfully; unchanged repository-wide mypy
   debt is disclosed.
10. The matching `PL-0174_CODEX_LOG_V03.md` exists, uses full GitHub URLs,
    records exact commands/results/SHAs/limitations and separate publication
    boundaries, and ends exactly `AWAITING_AUDIT`.
11. No OpenMVS/external-engine execution or discovery, `.mvs` writer, dense or
    later stage, orchestration, unrelated processing, schema/dependency/lock
    change, tracker or ChatGPT audit artifact edit, physical/native-device
    acceptance, or PL-0175+ implementation is included.

Closure requires a fresh independent ChatGPT audit of the V03 implementation
diff, source, tests, and handoff against every criterion.
