# PL-0354 - Codex Prompt V01

Task: **macOS GitHub Actions Swift build and tests**
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

Create a macOS GitHub Actions workflow for PackLab Capture Swift build and unit tests.

Use a currently supported macos runner/Xcode selected explicitly or reported in provenance. Resolve the checked-in Xcode project, build the iOS Simulator target without signing, and run PackLabCaptureTests on an available simulator destination. Use least-privilege contents:read, timeout, pull_request/relevant push/workflow_dispatch triggers and no secrets.

Capture xcodebuild version, SDK/simulator destination and test summary as nonsecret provenance.

## Handoff

Publish implementation/evidence commit(s), then `coordination/sessions/M16-C001/PL-0354_CODEX_LOG_V01.md` as a distinct log-only commit. Record exact runner/Xcode/build/signing facts without secrets.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
