# PL-0359 - Codex Prompt V01

Task: **Free-first unsigned fallback and installation route**
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

Implement/document the free-first fallback when CI signing is unavailable.

Publish the unsigned simulator/device archive artifacts from PL-0356/0357 with explicit limitations. Document supported installation routes truthfully:
- simulator app installation through Xcode/simctl on macOS;
- physical iPhone installation requires valid Apple signing and provisioning;
- local Xcode personal-team/free provisioning may be used where Apple permits;
- if documenting any Windows-side community sideload/sign tooling, keep it optional/user-managed, do not bundle it, distinguish it from an Apple-official PackLab path, and state credential/privacy implications.

Do not claim that an unsigned .app/.xcarchive can directly install on iPhone 16.

## Handoff

Publish implementation/evidence commit(s), then `coordination/sessions/M16-C001/PL-0359_CODEX_LOG_V01.md` as a distinct log-only commit. Record exact runner/Xcode/build/signing facts without secrets.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
