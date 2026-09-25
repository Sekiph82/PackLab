# M05-BATCH-001 — Master Codex Work Order V01

Milestone: **M05 — Transfer & Ingest**
Tasks: **PL-0119 through PL-0134** (16 tasks)
Repository: https://github.com/Sekiph82/PackLab
Branch: main
Canonical tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
This master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
Master audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md
Required master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_LOG_V01.md

## Authorization gate

Before material work, TASKS.md must show:
- Current Milestone: M05
- Current Sprint: M05-BATCH-001
- Current Task: M05-BATCH-001
- Current Task Status: READY
- Required Actor: CODEX
- M03 and M04 marked complete
- PL-0068 still unchecked / OWNER_REQUIRED
- M06 not started
- Next Task/Action pointing to this master prompt

Otherwise stop TASK_STATE_MISMATCH.

Before work:
- git fetch origin main --prune
- git rev-list --left-right --count HEAD...origin/main
- git status --porcelain

Fast-forward only when safe. Never reset, rebase, force-push, destructively clean or stash owner work.

Never edit root TASKS.md or ChatGPT audit artifacts. Never start M06. Never fabricate PL-0068 physical evidence.

## Product outcome

At the end of M05 there must be two real ways to move a finalized scan off the iPhone:

1. **System Share Sheet**  
   Finalized .packscan can be sent through standard iOS destinations such as Files/iCloud Drive/AirDrop/other installed share targets.

2. **Direct local-network transfer to PackLab Studio receiver**  
   iPhone pairs with the intended Windows receiver, uploads the finalized .packscan securely/resumably, receiver verifies it, then passes it through the same Windows ingest pipeline.

The direct receiver target in M05 is Windows Studio. Do not invent a separate macOS Studio application in this milestone. macOS can receive the finalized package through standard iOS share destinations where supported.

## Existing authority to preserve

Reuse:
- PackScanWriter and canonical PackScan 1.0 schemas;
- M03/M04 finalized session/package lifecycle;
- immutable accepted source evidence;
- Python packlab_core.packscan.validate_packscan / safe extraction as the Windows validation authority;
- privacy/secrets/signing rules;
- no M06 PySide6 application shell yet.

Do not create a second PackScan writer or an alternate mutable transfer package format.

## Transfer protocol architecture

Implement one versioned **PackLab Transfer Protocol V1**.

Required flow:

Windows receiver start
→ ephemeral/local TLS identity ready
→ short-lived pairing offer/code + QR
→ iPhone verifies/pins receiver identity and pairs
→ iPhone creates transfer with capture ID, byte size and whole-package SHA-256
→ receiver returns transfer ID / confirmed offset
→ resumable chunk transfer
→ receiver independently hashes completed bytes
→ only checksum-verified package enters Capture Inbox
→ common Windows ingest pipeline validates PackScan
→ immutable raw evidence + import index + report
→ authenticated verified completion acknowledgement to iPhone.

### Security contract

- Production local transfer must be encrypted with standard TLS/platform cryptography.
- Do not implement custom encryption primitives.
- Pairing must bind iPhone to the intended receiver using short-lived pairing material and receiver certificate fingerprint/pinning identity.
- Reject unpaired, expired, replayed, wrong-receiver, wrong-pin and insecure/downgraded sessions.
- Private keys, bearer/session credentials and long-lived secrets must never enter Git, QR payloads, PackScan files, logs or diagnostics.
- Any required Python networking/crypto/QR dependency must be minimal, license-compatible, declared in pyproject.toml, locked in uv.lock, and covered by existing dependency/license policy. Do not use untracked pip installs.

## Windows UI boundary

M05 implements ingest application/controller surfaces for:
- dropped .packscan paths;
- file-picker selected .packscan paths;
- Capture Inbox packages from the network receiver.

Do not build the full M06 PySide6 shell/navigation/workspaces early. M06 will visually host these M05 services later. M05 must nevertheless provide real, testable application entry points and structured results, not TODO stubs.

## Ordered children

### 1. PL-0119 — .packscan finalization with checksums and atomic rename

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

### 2. PL-0120 — iOS Share Sheet export

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0120_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0120_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0120_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

### 3. PL-0121 — Local-network transfer protocol V1

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

### 4. PL-0122 — QR and pairing-code workflow

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

### 5. PL-0123 — Encrypted/authenticated local transfer

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

### 6. PL-0124 — Resumable large-package transfer

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

### 7. PL-0125 — Post-transfer checksum verification

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

### 8. PL-0126 — Transfer progress, cancel and retry UI

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

### 9. PL-0127 — Windows drag/drop and file-picker ingest entry points

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0127_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0127_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0127_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

### 10. PL-0128 — Windows paired network receiver

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0128_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0128_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0128_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

### 11. PL-0129 — Schema/checksum validation before extraction

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0129_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0129_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0129_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

### 12. PL-0130 — Quarantine corrupt/unsupported scans

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0130_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0130_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0130_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

### 13. PL-0131 — Immutable raw-ingest copy

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0131_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0131_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0131_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

### 14. PL-0132 — Import report generation

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

### 15. PL-0133 — Deduplicate by capture ID/checksum

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0133_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0133_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0133_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

### 16. PL-0134 — Ingest resilience integration tests

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, preserve accepted M02/M03/M04 contracts, implement only this task, add behavior-bearing tests, create one implementation/evidence commit, then publish a separate child log-only commit ending READY_FOR_INDEPENDENT_AUDIT.

## Integration gate after PL-0126 — iPhone export/transfer

Prove one coherent iOS flow:

finalized scan
→ share sheet OR paired receiver
→ authenticated TLS session
→ create transfer
→ resume-aware chunk upload
→ progress/cancel/retry
→ receiver whole-package checksum verification
→ authenticated completion acknowledgement.

Requirements:
- only finalized .packscan files are transferable;
- cancellation never deletes immutable/finalized source evidence;
- retry resumes authoritative confirmed bytes;
- sender never marks complete before checksum-verified receiver acknowledgement;
- pairing/transfer secrets are redacted.

## Integration gate after PL-0134 — Windows ingest

Prove one coherent ingest flow:

manual file/drop OR verified network inbox
→ PackScan validation
→ invalid package quarantine
→ valid immutable raw package copy
→ capture ID/digest dedupe
→ safe extraction/ingest metadata
→ structured import report.

Requirements:
- validation occurs before extraction;
- invalid/incomplete network data never enters normal import authority;
- raw source evidence is never silently modified;
- same capture ID/digest is idempotent;
- identity conflicts never overwrite;
- interrupted transfer can resume and import exactly once.

## Dependency/build gate

If M05 requires new Python runtime dependencies for HTTPS server, certificate generation, QR generation or related functionality:
- choose mature standard libraries/packages rather than custom crypto/network parsers;
- add compatible version constraints to project dependencies;
- update uv.lock;
- ensure Windows bootstrap remains reproducible;
- record license implications if the repository license register requires it;
- keep the full locked test suite green.

Do not weaken TLS/certificate validation merely to avoid a dependency.

## Per-child execution discipline

For every child:
1. read TASKS.md, this master prompt/criteria, child prompt and child criteria;
2. verify authorization remains valid;
3. inspect current main, including earlier M05 child changes;
4. implement only the frozen child scope;
5. add behavior-bearing success/failure/restart/security tests;
6. run focused tests plus relevant regression/project/static checks;
7. run git diff --check;
8. prove TASKS.md and ChatGPT audits are untouched;
9. review secrets/signing/private/caches;
10. create a distinct implementation/evidence commit;
11. publish the child log in a separate log-only commit;
12. verify remote visibility before continuing.

## STOP conditions

Stop the batch if:
- authorization/repository safety fails;
- a task requires M06/later-milestone implementation;
- a genuine owner/ADR decision is required;
- a security requirement would be weakened or bypassed;
- protected files would need Codex edits;
- secrets/signing/private material risk appears;
- full locked tests cannot run truthfully;
- physical/native network evidence would need fabrication.

On STOP publish truthful evidence and end the master log BATCH_STOPPED.

## Final validation

After all 16:
- M03/M04 accepted behavior remains unregressed;
- PL-0068 remains OWNER_REQUIRED;
- no M06 implementation;
- full declared locked Python suite passes;
- relevant iOS source/static/project checks pass;
- Windows ingest/transfer integration tests pass;
- git diff --check passes;
- TASKS.md/ChatGPT audits untouched;
- privacy/signing/secrets/cache review clean;
- every child has a distinct implementation commit and log-only commit.

Native Xcode/iPhone/real-LAN/AirDrop results may be claimed only if actually executed. Loopback/source tests are not physical-device validation.

## User-facing link policy

Every user-facing repository reference must be a full GitHub URL. Never show local checkout/file paths.

## Final handoff

Publish:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_LOG_V01.md

The master log must index all 16 children with:
- full GitHub prompt/criteria/log links;
- start commit;
- implementation commit;
- log publication commit;
- validation results;
- security/privacy evidence;
- native/physical limitations.

End exactly:

AWAITING_MILESTONE_AUDIT

Stop. Do not self-audit.
