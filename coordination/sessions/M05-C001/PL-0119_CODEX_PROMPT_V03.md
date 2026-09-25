# PL-0119 — Codex Remediation Work Order V03

Task: **PL-0119 — Canonical production finalization and complete failure matrix**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CODEX_LOG_V03.md

## Authorization

TASKS.md must authorize `M05-BATCH-003 / READY / CODEX`. Preserve accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 plus accepted M03/M04. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Read the V02 audit first. Preserve useful implementation and close exactly these remaining gaps.

## Mandatory remediation

1. Keep CanonicalFinalizationSource and the existing PackScanWriter/SessionFinalizer rollback design.
2. Route the actual production finalization call through SessionFinalizer.finalize(source:manifest:payloads:destination:) so authoritative accepted records + immutable source/metadata bytes are required in the real app flow.
3. Add deterministic tests for CanonicalFinalizationSource success and missing authoritative source/metadata rejection.
4. Add real filesystem/injected failure tests for package write/move failure, finalization-record publication failure, destination-already-exists, checksum failure and no-partial destination/finalization/temp artifacts.
5. After every injected failure prove the session remains resumable and any pre-existing valid exported package/finalization record is preserved or restored truthfully.

## Validation

Tests must drive production-used seams, not a parallel helper. Run focused tests, full locked suite, relevant Swift/project/static checks, Ruff/compileall, `git diff --check`, protected-file and secrets/privacy/signing checks. Native/physical claims only if genuinely executed.

Create one implementation/evidence commit and one separate V03 log-only commit. All user-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
