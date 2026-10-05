# PL-0358 - Codex Prompt V01

Task: **Optional secret-safe signed IPA path**
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

Implement an optional GitHub Actions signed IPA/export path that runs only when explicitly configured signing credentials are available in a protected context.

Use repository/environment secrets only by secret name, never literal values. Recommended pattern: base64-encoded signing certificate + password, provisioning profile, Apple team/bundle/export metadata as protected secrets/vars; create an ephemeral runner keychain, import certificate with noninteractive security commands, install the profile transiently, archive/export with an explicit generated ExportOptions.plist, and scrub all temporary materials in an always() cleanup step.

Never run this job on fork pull requests. Avoid command echo of secret values. Do not upload certificates/profiles/keychains. The final artifact provenance must say SIGNED and record nonsecret identity such as team ID/profile UUID only if safe.

## Handoff

Publish implementation/evidence commit(s), then `coordination/sessions/M16-C001/PL-0358_CODEX_LOG_V01.md` as a distinct log-only commit. Record exact runner/Xcode/build/signing facts without secrets.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
