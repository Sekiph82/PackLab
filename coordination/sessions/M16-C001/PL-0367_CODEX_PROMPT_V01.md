# PL-0367 - Codex Prompt V01

Task: **Rollback for incompatible Capture/Studio versions**
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

Document and implement a deterministic compatibility/rollback playbook for incompatible Capture/Studio/PackScan combinations.

Cover detection of unsupported schema, preserving original .packscan evidence, selecting a previously supported Studio/Capture artifact by release manifest, non-destructive migration where supported, downgrade limitations, restoring prior project/library backup where relevant, reinstallation steps for Capture, and how to verify exact version/build after rollback.

Do not prescribe in-place mutation of raw .packscan evidence. Do not promise downgrade compatibility where no declared path exists.

## Handoff

Publish implementation/evidence commit(s), then `coordination/sessions/M16-C001/PL-0367_CODEX_LOG_V01.md` as a distinct log-only commit. Record exact version/provenance facts and limitations.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
