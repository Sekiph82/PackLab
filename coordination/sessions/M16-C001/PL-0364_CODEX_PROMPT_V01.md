# PL-0364 - Codex Prompt V01

Task: **Release manifest with dependencies and compatibility**
Milestone: **M16 - CI/CD, Signing & Distribution**
Cycle: **M16-C001**

## M16 release rules

- Read live TASKS.md, M15 final audit, versioning policy, dependency/license register, M16 predecessor prompts/criteria and exact current version sources.
- Root TASKS.md is ChatGPT-owned; Codex must not edit it.
- StudioVersion, CaptureVersion and PackScanSchemaVersion are distinct domains. Do not force numerical equality.
- Current observed baselines are Studio 0.1.0, Capture 0.1.0, PackScan schema 1.0.0 unless source changes before execution.
- Release metadata binds semantic versions plus commit/build provenance; a SHA never replaces a semantic version.
- No release manifest/changelog/checklist may imply M17 acceptance that has not occurred.
- No Git tag/GitHub Release/V0.1 release publication is authorized before PL-0368 and its M17 gate.
- Secrets/private artifacts/signing material remain excluded.
- Every executable child publishes implementation/evidence then separate log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

## Required implementation

Create a deterministic machine-readable release manifest contract generated from authoritative source/build facts.

Include release train ID, Studio/Capture/PackScan versions, commit SHA, Windows/iOS artifact provenance references, Python/Qt/OCP/OCCT/Open3D build dependency versions actually shipped, Xcode/Swift/NextLevel identity, supported PackScan read/write schema range, migration support declarations, signing state per artifact, third-party notice/inventory reference, and known limitations.

Manifest generation must fail closed when a required artifact/provenance/compliance reference is missing. Paths must be logical/relative, never owner-absolute. Do not claim M17 acceptance.

## Handoff

Publish implementation/evidence commit(s), then `coordination/sessions/M16-C001/PL-0364_CODEX_LOG_V01.md` as a distinct log-only commit. Record exact version/provenance facts and limitations.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
