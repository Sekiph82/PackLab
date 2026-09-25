# M05-BATCH-002 — Master Remediation Codex Work Order V01

Milestone: **M05 — Transfer & Ingest**
Purpose: **Close the 13 failed M05 children from Batch-001**
Authorized tasks: **PL-0119–PL-0126, PL-0128, PL-0130, PL-0132, PL-0133, PL-0134**
Accepted/excluded children: **PL-0127, PL-0129, PL-0131**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Canonical tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
Previous master audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CHATGPT_AUDIT_V01.md
This master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Master criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V01.md
Required master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_LOG_V01.md

## Authorization gate

Before material work, TASKS.md must show:
- Current Milestone: M05
- Current Sprint: M05-BATCH-002
- Current Task: M05-BATCH-002
- Current Task Status: READY
- Required Actor: CODEX
- PL-0127, PL-0129 and PL-0131 checked/accepted
- the 13 authorized remediation children unchecked
- M03/M04 accepted
- PL-0068 unchecked / OWNER_REQUIRED
- M06 not started
- Next Task/Action pointing to this master remediation prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Before work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Fast-forward only if safe. Never reset, rebase, force-push, destructively clean or stash owner work.

Never edit root TASKS.md or ChatGPT audit artifacts. Never start M06. Never fabricate PL-0068 evidence.

## Preserve accepted M05 work

Do not regress:
- PL-0127: common manual drop/file-picker ingest boundary;
- PL-0129: authoritative PackScan validation before extraction;
- PL-0131: immutable raw evidence store.

M03/M04 capture/session/package behavior must also remain intact.

## Remediation architecture

Batch-001 produced many good components but left them disconnected. Batch-002 must converge on **one production transfer/export architecture**.

### iPhone export flow

Finalized authoritative scan
→ eligibility from SessionFinalizationRecord
→ user chooses **Share** or **Send to PackLab**
→ Share uses system UIActivityViewController
OR
→ Send to PackLab opens pairing/receiver UI
→ QR/manual pairing establishes pinned receiver identity
→ short-lived pairing exchange returns scoped session credential
→ production iOS URLSession client uses certificate pinning + Bearer auth
→ create/query/chunk/cancel/resume/complete via Transfer Protocol V1
→ TransferViewModel/SwiftUI reflects confirmed receiver state only
→ sender becomes completed only after authenticated verified digest acknowledgement.

`TransferService` must no longer be left as the production `UnavailableTransferService` path for M05.

### Windows receiver/ingest flow

HTTPS receiver start
→ network pairing/auth
→ authenticated create/status/chunk/cancel/complete
→ persisted resumable .part/checkpoint
→ whole-package SHA-256 verification
→ verified Capture Inbox publication only
→ common PL-0127 ImportService
→ PL-0129 validation
→ PL-0130 quarantine if invalid
→ PL-0131 immutable raw store if valid
→ PL-0133 dedupe/index authority
→ PL-0132 structured report
→ exactly-once normal import result.

Do not create parallel validators, PackScan writers, raw stores or receiver-specific ingest logic.

## Security rules

- Standard TLS/platform cryptography only.
- No custom encryption.
- No insecure HTTP production fallback.
- Receiver certificate fingerprint must be pinned from the pairing offer.
- Pairing codes/offers are short-lived and replay-safe.
- Long-lived private keys remain local/outside Git.
- Bearer/session credentials are scoped/expiring and never logged or persisted into PackScan.
- QR may contain only the permitted short-lived pairing offer data and non-secret certificate fingerprint.
- Any new dependency must be declared/locked/reproducible.

## Ordered children

Execute exactly these 13 tasks in order:

### 1. PL-0119 — Finalization failure-matrix and production authority closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CODEX_LOG_V02.md

Read the previous audit first. Preserve useful V01 implementation, close only the frozen V02 gaps, add production-seam tests, create a distinct implementation/evidence commit, then publish a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 2. PL-0120 — Production Share Sheet workflow closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0120_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0120_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0120_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0120_CODEX_LOG_V02.md

Read the previous audit first. Preserve useful V01 implementation, close only the frozen V02 gaps, add production-seam tests, create a distinct implementation/evidence commit, then publish a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 3. PL-0121 — Complete cross-language Transfer Protocol V1 contract

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CODEX_LOG_V02.md

Read the previous audit first. Preserve useful V01 implementation, close only the frozen V02 gaps, add production-seam tests, create a distinct implementation/evidence commit, then publish a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 4. PL-0122 — Production pairing UI, QR/manual workflow and reconnect identity

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CODEX_LOG_V02.md

Read the previous audit first. Preserve useful V01 implementation, close only the frozen V02 gaps, add production-seam tests, create a distinct implementation/evidence commit, then publish a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 5. PL-0123 — Production TLS/auth pairing and pinned iOS network client

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CODEX_LOG_V02.md

Read the previous audit first. Preserve useful V01 implementation, close only the frozen V02 gaps, add production-seam tests, create a distinct implementation/evidence commit, then publish a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 6. PL-0124 — Production sender reconnect/resume closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CODEX_LOG_V02.md

Read the previous audit first. Preserve useful V01 implementation, close only the frozen V02 gaps, add production-seam tests, create a distinct implementation/evidence commit, then publish a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 7. PL-0125 — End-to-end verified completion closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_LOG_V02.md

Read the previous audit first. Preserve useful V01 implementation, close only the frozen V02 gaps, add production-seam tests, create a distinct implementation/evidence commit, then publish a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 8. PL-0126 — Production iOS transfer screen and network-bound cancel/retry

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_LOG_V02.md

Read the previous audit first. Preserve useful V01 implementation, close only the frozen V02 gaps, add production-seam tests, create a distinct implementation/evidence commit, then publish a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 9. PL-0128 — Authenticated HTTPS receiver lifecycle integration closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0128_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0128_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0128_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0128_CODEX_LOG_V02.md

Read the previous audit first. Preserve useful V01 implementation, close only the frozen V02 gaps, add production-seam tests, create a distinct implementation/evidence commit, then publish a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 10. PL-0130 — Complete quarantine evidence matrix

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0130_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0130_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0130_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0130_CODEX_LOG_V02.md

Read the previous audit first. Preserve useful V01 implementation, close only the frozen V02 gaps, add production-seam tests, create a distinct implementation/evidence commit, then publish a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 11. PL-0132 — Complete import-report golden matrix

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CODEX_LOG_V02.md

Read the previous audit first. Preserve useful V01 implementation, close only the frozen V02 gaps, add production-seam tests, create a distinct implementation/evidence commit, then publish a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 12. PL-0133 — Structured identity conflicts and index reconstruction closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0133_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0133_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0133_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0133_CODEX_LOG_V02.md

Read the previous audit first. Preserve useful V01 implementation, close only the frozen V02 gaps, add production-seam tests, create a distinct implementation/evidence commit, then publish a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 13. PL-0134 — True cross-language transfer-to-ingest integration closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_LOG_V02.md

Read the previous audit first. Preserve useful V01 implementation, close only the frozen V02 gaps, add production-seam tests, create a distinct implementation/evidence commit, then publish a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

## Integration gate after PL-0126 — real iPhone sender/export stack

Prove one coherent production composition:
- finalized package eligibility;
- real Share action from finalized history;
- real pairing UI;
- manual code and QR parse/scan path;
- production camera ownership handoff for scanner;
- persisted non-secret receiver reconnect identity;
- pinned TLS URLSession client;
- network pairing endpoint;
- authenticated create/status/chunk/cancel/resume/complete;
- sender reconnect/resume from confirmed offset;
- verified digest acknowledgement;
- actual SwiftUI progress/cancel/retry screen.

The tests may use deterministic fake URLProtocol/client transports where native socket execution is unavailable, but the **same production iOS client/coordinator** must be exercised. Do not replace it with test-only policy helpers.

## Integration gate after PL-0128 — real receiver transport

Use ephemeral local certificates and loopback HTTPS where available in Python tests.

Prove:
- server actually starts with TLS;
- pairing/auth happens through the network endpoint;
- missing auth is rejected;
- partial upload survives stop/restart;
- status query returns authoritative offset;
- resumed upload completes;
- concurrent transfer IDs remain isolated;
- only verified packages enter Capture Inbox.

## Integration gate after PL-0134 — end-to-end authority

Prove:
paired/pinned sender
→ HTTPS receiver
→ resumed verified package
→ Capture Inbox
→ PackScan validation
→ quarantine or immutable raw store
→ dedupe/index
→ import report.

Also prove:
- internal checksum mismatch quarantine;
- true future-schema quarantine;
- unsafe path quarantine;
- corrupt ZIP quarantine;
- declared image/photo payload specifically missing while control files remain otherwise valid;
- identity conflicts retain both digests and never overwrite;
- same scan transfer/import is exactly-once.

## Per-child discipline

For every child:
1. read TASKS.md, this master prompt/criteria, V02 child prompt/criteria and V01 audit;
2. inspect current `main`;
3. implement only the authorized remediation;
4. add production-seam behavior tests;
5. run focused tests;
6. run full locked suite;
7. run relevant iOS project/static checks and Python Ruff/compileall checks;
8. run `git diff --check`;
9. verify TASKS.md/ChatGPT audits untouched;
10. review secrets/private keys/signing/caches;
11. create one implementation/evidence commit;
12. publish the V02 child log in a separate log-only commit;
13. verify remote visibility before continuing.

## STOP conditions

Stop the batch if:
- authorization/repository safety fails;
- a fix requires M06/later milestone implementation;
- a genuine owner/ADR decision is required;
- security would have to be weakened/bypassed;
- protected files would need Codex edits;
- secrets/private material risk appears;
- full locked suite cannot run truthfully;
- physical/native evidence would need fabrication.

If stopped, publish truthful evidence and end master log `BATCH_STOPPED`.

## Final validation

After all 13:
- accepted PL-0127/PL-0129/PL-0131 remain green;
- M03/M04 remain accepted;
- PL-0068 remains OWNER_REQUIRED;
- no M06 implementation;
- full locked suite passes;
- transfer/security/ingest integration tests pass;
- relevant iOS project/static checks pass;
- Ruff/compileall pass;
- `git diff --check` passes;
- TASKS.md/ChatGPT audits untouched;
- secret/private-key/signing scan clean;
- each remediation child has distinct implementation and log-only commits.

Native Xcode/iPhone/AirDrop/real-LAN execution may be claimed only if genuinely executed. Deterministic production-client tests and local loopback tests must not be mislabeled as physical-device validation.

## User-facing link policy

Every user-facing repository reference must be a full GitHub URL. Never output local filesystem paths.

## Final handoff

Publish:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_LOG_V01.md

The master log must index all 13 children with full GitHub prompt/criteria/audit/log links, exact implementation/log commits, tests, security evidence and limitations.

End exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not self-audit.
