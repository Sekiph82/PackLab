# PL-0119 — Codex Remediation Work Order V04

Task: **PL-0119 — Wire canonical finalization into real app export flow**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CODEX_LOG_V04.md

TASKS.md must authorize `M05-BATCH-004 / READY / CODEX`. Preserve all 10 accepted M05 children, accepted M03/M04, and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Preserve the accepted architecture. Close only the final independent-audit gap.

## Mandatory remediation

1. Preserve CanonicalSessionFinalizationWorkflow, SessionGalleryStore.finalizeAcceptedSession and the now-green injected rollback/failure matrix.
2. Add a real production scan-finalize/export action reachable from the active session/history workflow that invokes the canonical source-only finalization seam; do not call arbitrary SessionFinalizer.finalize(FinalizationInput...) from production UI.
3. Build manifest/payload inputs only from canonical accepted-session records, immutable source bytes and accepted metadata contracts.
4. After successful finalization, prove the resulting finalization record/history entry becomes exported and is immediately eligible for Share/Send-to-PackLab.
5. Add a production-workflow test for accepted session → canonical finalization → exported history, plus missing-authority failure with no exported state.

Run production-seam behavior tests, full locked suite, relevant Swift/project/static checks, Ruff/compileall, `git diff --check`, protected-file and privacy/secret checks. Native/physical claims only if genuinely executed.

Create one implementation/evidence commit and one separate V04 log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
