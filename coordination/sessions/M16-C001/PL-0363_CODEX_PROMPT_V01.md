# PL-0363 - Codex Prompt V01

Task: **Coordinated release numbering across Studio, Capture and PackScan**
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

Implement a canonical release-version model/tooling that reads/validates the three independent version domains:
- StudioVersion from PackLab Studio source/build metadata;
- CaptureVersion + numeric build from Xcode project/Info.plist settings;
- PackScanSchemaVersion from the core container/schema contract.

Define an internal release train identifier that can coordinate artifacts without requiring the three semantic versions to match numerically. Provide validation that each value is SemVer-compatible according to VERSIONING_POLICY and that build metadata records exact commit.

If updating version sources to prepare an internal 0.1 release train, preserve current compatible values unless a documented public contract requires a bump. Do not create a Git tag or release.

## Handoff

Publish implementation/evidence commit(s), then `coordination/sessions/M16-C001/PL-0363_CODEX_LOG_V01.md` as a distinct log-only commit. Record exact version/provenance facts and limitations.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
