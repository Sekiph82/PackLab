# PL-0366 - Codex Prompt V01

Task: **Release checklist requiring Windows and iOS audits**
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

Create a release checklist/gate validator requiring both Windows and iOS build/distribution audit evidence before a release candidate can advance.

Require at minimum:
- Windows CI/build/package/smoke PASS;
- redistribution inventory/third-party notices PASS;
- macOS Swift tests/simulator build PASS;
- unsigned archive PASS and signed IPA PASS only when a signed release artifact is intended;
- secrets scan PASS;
- artifact provenance/digests present;
- M17 acceptance gate status as an explicit future requirement;
- outstanding physical-validation/known limitations surfaced.

The validator must fail closed on missing/stale audit IDs and never infer independent acceptance from Codex logs.

## Handoff

Publish implementation/evidence commit(s), then `coordination/sessions/M16-C001/PL-0366_CODEX_LOG_V01.md` as a distinct log-only commit. Record exact version/provenance facts and limitations.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
