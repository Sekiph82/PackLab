# PL-0125 — Codex Work Order V01

Task: **PL-0125 — Post-transfer checksum verification**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03 and M04 must remain accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M06.

Reuse the accepted M02 PackScan contracts and M03/M04 session/finalization architecture. Do not create parallel package writers, camera/session owners or mutable export formats.

## Mandatory implementation

1. Use the whole-package SHA-256 declared at transfer creation as the end-to-end package identity.
2. After all bytes arrive, receiver must independently hash the completed `.part` file before any final publication/import acknowledgement.
3. A checksum mismatch must retain/quarantine diagnostic evidence according to policy but must never mark transfer/export complete or publish the file as a valid inbox package.
4. Sender may mark network export complete only after an authenticated receiver acknowledgement that includes the matching transfer/package digest.
5. Persist verification result and bytes/expected/actual digest metadata without leaking private paths or secrets.
6. Add tests for matching digest, final-byte corruption, wrong declared digest, retry after mismatch, and sender state not completing before verified acknowledgement.

## Validation

Add behavior-bearing success, failure, cancellation, restart and exact-boundary tests appropriate to the task. Run focused tests, the full declared locked suite, relevant iOS/static/project checks, `git diff --check`, protected-file checks, and privacy/signing/secret review. Native iPhone/Xcode/network hardware claims may be made only if genuinely executed.

Create one implementation/evidence commit and then a separate child log-only commit. Every user-facing repository link must be a full GitHub URL, never a local filesystem path.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
