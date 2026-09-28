# PL-0179 - ChatGPT Audit Criteria V03

Task: **Preserve all reconstruction stage outputs and logs for reproducibility**

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CHATGPT_AUDIT_V02.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CODEX_PROMPT_V03.md

All criteria below are mandatory for closure of PL-0179 V03.

1. Root `TASKS.md` authorizes PL-0179 V03 with status `CHANGES_REQUIRED` and
   Required Actor `CODEX`; PL-0178 remains `AUDITED_PASS`, PL-0068 remains
   `OWNER_REQUIRED`, and PL-0180+ remains unauthorized.
2. The V03 diff is limited to the existing retention implementation, its
   public tests, and the matching V03 log. V01/V02 evidence, accepted
   predecessor behavior, tracker state, audit artifacts, schemas,
   dependencies, locks, and protected files are preserved.
3. All V02 collision and integrity behavior remains intact: case-insensitive
   source/output/identity/stage-run collisions, duplicate sequence basenames,
   mapping-form determinism, manifest provenance, and retained path/size/SHA
   validation on idempotent retry.
4. Final evidence publication is atomic at the stage/run identity boundary,
   or rollback is verified so every failure after any staged-child movement
   leaves no final identity and cannot silently accept an uncleared partial
   directory. Prior evidence is never deleted or replaced on a same-identity
   collision.
5. A public failure-injection test through the retainer boundary fails during
   final publication and proves the final identity is absent afterward. The
   test is behavior-sensitive and does not merely inspect implementation
   details.
6. The normal success/failure/cancelled, partial-output, bounded-log,
   missing-output, provenance, idempotent, source-preserving, and V01/V02
   regression behavior remains intact.
7. The manifest contract remains unchanged and deterministic, with contract
   version, stage/run identity, source revision/digest, status, exit code,
   duration, redacted stdout/stderr, retained paths, sizes, SHA-256 digests,
   provenance/request/stage digests, and output identities.
8. The exact locked full suite exits `0`; no new skip/xfail hides a finding,
   and unavailable `cv2`, symlink privilege, warnings, and absent OpenMVS
   executable are reported truthfully.
9. Ruff, format, targeted mypy, compileall, diff, protected-file/scope,
   dependency/lock, privacy/secrets/signing, generated/binary, and
   remote-visibility checks pass truthfully; unchanged repository-wide mypy
   debt is disclosed.
10. `PL-0179_CODEX_LOG_V03.md` uses full GitHub URLs, records exact commands,
    results, SHAs, limitations, scope, and separate publication boundaries,
    and ends exactly `AWAITING_AUDIT` without predeclaring its future log
    commit SHA.
11. No private/confidential data, generated reconstruction output, source/raw
    authority mutation, cleanup/expiry policy, physical/native-device
    acceptance, tracker or ChatGPT-audit edit by Codex, or PL-0180+
    implementation is included.

Closure requires a fresh independent ChatGPT audit of the V03 diff, source,
tests, and handoff against every criterion.
