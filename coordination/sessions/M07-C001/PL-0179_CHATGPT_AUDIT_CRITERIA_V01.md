# PL-0179 - ChatGPT Audit Criteria V01

Task: **Preserve all reconstruction stage outputs and logs for reproducibility**

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0178_CHATGPT_AUDIT_V01.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CODEX_PROMPT_V01.md

All criteria below are mandatory for closure of PL-0179 V01.

1. Root `TASKS.md` authorizes PL-0179 V01 with status `READY` and Required
   Actor `CODEX`; PL-0178 remains `AUDITED_PASS`, PL-0068 remains
   `OWNER_REQUIRED`, and PL-0180+ remains unauthorized.
2. The diff is limited to the local reconstruction-evidence retention boundary,
   its public tests, and the matching V01 log. Accepted PL-0178 and predecessor
   behavior, tracker state, audit artifacts, schemas, dependencies, locks, and
   protected files are preserved.
3. The public retention boundary accepts explicit workspace/stage/run/result
   inputs, preserves success/failure/cancellation evidence including partial
   outputs and bounded logs, and never deletes or silently replaces prior
   evidence.
4. Workspace, stage, run, output, and log identities are safe and revision
   scoped. Absolute/traversal/private/supplier paths, symlink escapes, unsafe
   identities, collisions, and raw/source-path targets fail through PackLab-
   owned errors.
5. The machine-readable manifest is deterministic and records contract version,
   stage/run identity, source revision/digest, status, exit code, duration,
   redacted stdout/stderr, retained relative paths, sizes, SHA-256 digests,
   provenance/request/stage digests, and output identities without parsing
   engine output contents.
6. Identical repeated retention is idempotent; same-identity byte or provenance
   mismatch fails closed and leaves prior evidence unchanged. Atomic writes and
   bounded text handling are used, and missing/unreadable explicit outputs are
   reported rather than fabricated.
7. The retention boundary is local-only and regeneration-aware. It adds no
   tracked reconstruction outputs, LFS/cleanup policy, orchestration, engine
   discovery/installation, CPU/GPU preset, mesh/texture parsing, quality,
   measurement, UI, schema/dependency/lock, or PL-0180+ work.
8. Public tests are behavior-sensitive through the public retention and
   manifest boundaries. They cover success/failure/cancellation, partial
   outputs, repeated identical retention, collisions/mismatches, unsafe paths,
   symlink escapes, bounded/redacted logs, missing/unreadable outputs, atomic
   failure behavior, provenance preservation, and predecessor regressions.
9. The exact locked full suite exits `0`; no new skip/xfail hides a finding, and
   unavailable `cv2`, symlink privilege, warnings, and absent OpenMVS
   executable are reported truthfully.
10. Ruff, format, targeted mypy, compileall, diff, protected-file/scope,
    dependency/lock, privacy/secrets/signing, generated/binary, and
    remote-visibility checks pass truthfully; unchanged repository-wide mypy
    debt is disclosed.
11. `PL-0179_CODEX_LOG_V01.md` uses full GitHub URLs, records exact commands,
    results, SHAs, limitations, scope, and separate publication boundaries,
    and ends exactly `AWAITING_AUDIT`.
12. No private or confidential data, generated reconstruction output, source
    evidence mutation, cleanup/deletion behavior, physical/native-device
    acceptance, tracker or ChatGPT-audit edit by Codex, or PL-0180+
    implementation is included.

Closure requires a fresh independent ChatGPT audit of the V01 diff, source,
tests, and handoff against every criterion.
