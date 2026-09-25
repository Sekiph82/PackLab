# PL-0134 — Codex Remediation Work Order V03

Task: **PL-0134 — Executable cross-language sender-to-receiver-to-ingest harness**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_LOG_V03.md

## Authorization

TASKS.md must authorize `M05-BATCH-003 / READY / CODEX`. Preserve accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 plus accepted M03/M04. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Read the V02 audit first. Preserve useful implementation and close exactly these remaining gaps.

## Mandatory remediation

1. Preserve the corrected missing-image fixture and all existing Windows ingest/quarantine assertions.
2. Replace the static Swift-source-string 'integration' check as milestone evidence with an executable cross-language transport contract harness.
3. The harness must exercise the same wire serialization, routes, transfer-ID persistence/resume semantics and completion validation used by URLSessionTransferClient against the real PackLabReceiver HTTPS endpoint. Prefer an Apple-capable Swift integration test when available; otherwise create a mechanically shared transport script/fixture generated from the Swift/Python authoritative protocol contract, not a source-text grep.
4. Exercise network pairing/auth, certificate pin identity, partial upload, sender same-ID restart/resume, receiver restart, cancel/retry, verified completion and exactly-once raw/index/report ingest in one coherent deterministic test chain.
5. Retain corrupt ZIP, bad manifest, internal checksum mismatch, future schema, unsafe path and isolated missing-declared-image quarantine coverage.
6. Static inspection may supplement but must not substitute for executable transport behavior.

## Validation

Tests must drive production-used seams, not a disconnected helper/static grep. Run focused tests, full locked suite, relevant Swift/project/static checks, Ruff/compileall, `git diff --check`, protected-file and secrets/privacy checks.

Create one implementation/evidence commit and one separate V03 log-only commit. All user-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
