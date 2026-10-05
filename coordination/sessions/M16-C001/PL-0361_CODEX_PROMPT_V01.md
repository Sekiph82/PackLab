# PL-0361 - Codex Prompt V01

Task: **Publish signed/unsigned artifacts with provenance**
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

Unify iOS artifact publication metadata so every simulator app, unsigned device archive and optional signed IPA has a machine-readable provenance sidecar.

Record artifact type, signing_state SIGNED/UNSIGNED, Capture version/build, PackScan schema, commit SHA, Xcode/SDK, bundle ID, SHA-256/byte length and workflow/run identifiers. Signed records may include nonsecret team/profile identity but never secret values. Artifact names must make signing state obvious and follow retention policy.

Validate sidecar digest against uploaded artifact before upload.

## Handoff

Publish implementation/evidence commit(s), then `coordination/sessions/M16-C001/PL-0361_CODEX_LOG_V01.md` as a distinct log-only commit. Record exact runner/Xcode/build/signing facts without secrets.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
