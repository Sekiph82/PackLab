# PL-0179 - ChatGPT Audit Criteria V02

Task: **Preserve all reconstruction stage outputs and logs for reproducibility**

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CHATGPT_AUDIT_V01.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CODEX_PROMPT_V02.md

All criteria below are mandatory for closure of PL-0179 V02.

1. Root `TASKS.md` authorizes PL-0179 V02 with status `CHANGES_REQUIRED` and
   Required Actor `CODEX`; PL-0178 remains `AUDITED_PASS`, PL-0068 remains
   `OWNER_REQUIRED`, and PL-0180+ remains unauthorized.
2. The V02 diff is limited to the existing PL-0179 retention implementation,
   its public tests, and the matching V02 log. V01 evidence, accepted
   predecessor behavior, tracker state, audit artifacts, schemas,
   dependencies, locks, and protected files are preserved.
3. The normal success/failure/cancelled, partial-output, bounded-log,
   missing-output, provenance, idempotent, and source-preserving behavior from
   V01 remains intact.
4. Case-insensitive source-path, retained-output-path, output-identity, and
   stage/run identity collisions fail through PackLab-owned errors before
   publication. No Windows-equivalent path may silently replace another
   retained output or evidence identity.
5. Sequence-form explicit output paths reject duplicate basenames before
   identity-map conversion; no explicit path is silently discarded. Mapping-
   form output behavior remains deterministic and collision-safe.
6. Final evidence publication is atomic at the stage/run boundary, or any
   failure after staged-child movement removes the final identity so no
   partial evidence directory remains. Prior evidence is never deleted or
   replaced on a same-identity collision.
7. Idempotent retry validates every retained output/log path, byte size, and
   SHA-256 digest against the manifest. Tampered or missing retained bytes and
   provenance mismatches fail closed through PackLab-owned errors and leave
   prior evidence unchanged.
8. The manifest remains deterministic and records contract version,
   stage/run identity, source revision/digest, status, exit code, duration,
   redacted stdout/stderr, retained relative paths, sizes, SHA-256 digests,
   provenance/request/stage digests, and output identities without parsing
   engine-specific contents.
9. Public tests are behavior-sensitive through the public retention and
   manifest boundaries. They cover the V01 regressions plus case-insensitive
   collisions, duplicate sequence basenames, injected mid-publication failure,
   retained-byte tampering, and predecessor regressions.
10. The exact locked full suite exits `0`; no new skip/xfail hides a finding,
    and unavailable `cv2`, symlink privilege, warnings, and absent OpenMVS
    executable are reported truthfully.
11. Ruff, format, targeted mypy, compileall, diff, protected-file/scope,
    dependency/lock, privacy/secrets/signing, generated/binary, and
    remote-visibility checks pass truthfully; unchanged repository-wide mypy
    debt is disclosed.
12. `PL-0179_CODEX_LOG_V02.md` uses full GitHub URLs, records exact commands,
    results, SHAs, limitations, scope, and separate publication boundaries,
    and ends exactly `AWAITING_AUDIT` without predeclaring its future log
    commit SHA.
13. No private/confidential data, generated reconstruction output, source
    evidence mutation, cleanup/deletion policy, physical/native-device
    acceptance, tracker or ChatGPT-audit edit by Codex, or PL-0180+
    implementation is included.

Closure requires a fresh independent ChatGPT audit of the V02 diff, source,
tests, and handoff against every criterion.
