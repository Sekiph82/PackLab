# PL-0360 - Codex Prompt V01

Task: **Prevent Apple signing material in public repo**
Milestone: **M16 - CI/CD, Signing & Distribution**
Cycle: **M16-C001**

## M16 global rules

- Read live TASKS.md, M15 final audit, dependency/license register, versioning policy, secrets policy, and exact predecessor prompt/criteria.
- Root TASKS.md is ChatGPT-owned; Codex must not edit it.
- CI permissions are least-privilege; fork/PR jobs must not receive signing credentials.
- No Apple certificate, provisioning profile, private key, keychain, token, private scan, supplier file or proprietary artwork may be committed or uploaded unintentionally.
- Build caches contain reproducible dependency metadata only, never signing/private/project state.
- NextLevel is already pinned in the Xcode project at exact version 0.19.1; preserve or explicitly justify any change.
- Signed paths are optional and must fail closed/skip when credentials are absent. Unsigned simulator/archive paths remain green independently.
- Any temporary keychain/profile/certificate material must be created only on the runner, protected from logs, and deleted even on failure.
- No runtime cloud/network feature may be added to PackLab apps.
- Every child publishes implementation/evidence then distinct child-log-only commit ending READY_FOR_INDEPENDENT_AUDIT.
- M17+ implementation is unauthorized; PL-0368 is deferred until M17 acceptance gates complete.

## Required implementation

Add repository and CI guards ensuring Apple certificates, provisioning profiles, private keys, keychains and common signing-secret exports are never committed.

Extend .gitignore/security documentation and add a deterministic repository scan/check for extensions/signatures such as .p12, .pfx, .mobileprovision, .cer where policy forbids committed binary signing material, keychain files, PEM private-key headers and configured secret-name/value leakage. Allow only reviewed public documentation fixtures that contain no credential bytes.

CI must fail with redacted file/path evidence only; never print secret contents.

## Handoff

Publish implementation/evidence commit(s), then `coordination/sessions/M16-C001/PL-0360_CODEX_LOG_V01.md` as a distinct log-only commit. Record exact runner/Xcode/build/signing facts without secrets.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
