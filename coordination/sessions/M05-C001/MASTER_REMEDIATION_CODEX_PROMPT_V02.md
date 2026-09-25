# M05-BATCH-003 — Master Remediation Codex Work Order V02

Milestone: **M05 — Transfer & Ingest**
Purpose: **Close the final 9 open M05 children**
Authorized tasks: **PL-0119, PL-0121–PL-0126, PL-0132, PL-0134**
Accepted/excluded M05 children: **PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131, PL-0133**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Canonical tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
Previous master audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_V01.md
This master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Master criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V02.md
Required master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_LOG_V02.md

## Authorization gate

Before material work, TASKS.md must show:
- Current Milestone: M05
- Current Sprint: M05-BATCH-003
- Current Task: M05-BATCH-003
- Current Task Status: READY
- Required Actor: CODEX
- exactly these 7 M05 children checked: PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131, PL-0133
- exactly these 9 M05 children still unchecked: PL-0119, PL-0121, PL-0122, PL-0123, PL-0124, PL-0125, PL-0126, PL-0132, PL-0134
- M03/M04 accepted
- PL-0068 unchecked / OWNER_REQUIRED
- M06 not started
- Next Task/Action pointing to this master prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Before work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Fast-forward only if safe. Never reset, rebase, force-push, destructively clean or stash owner work.

Never edit TASKS.md or ChatGPT audit artifacts. Never start M06. Never fabricate PL-0068 evidence.

## Mission

This is not another broad feature batch. The architecture now exists. Close the final integration defects so M05 can be independently accepted.

The end state must be one coherent production chain:

canonical accepted session
→ canonical finalization source
→ finalized .packscan
→ Share OR Send to PackLab
→ functional manual/QR pairing
→ real capture-camera ownership handoff for QR
→ pinned HTTPS pairing/auth
→ persisted sender transfer identity
→ same transfer ID across retry/app restart
→ authoritative receiver next_offset resume
→ verified matching terminal acknowledgement
→ verified Capture Inbox
→ PackScan validation
→ quarantine OR immutable raw authority
→ dedupe/index
→ complete privacy-safe import report
→ executable end-to-end transport/ingest evidence.

## Non-negotiable defects to close

### Same-transfer resume
The current implementation may generate a new UUID during retry because the resolved transfer ID is not persisted back into the production request/state. Batch-003 must make same-ID resume mechanically true and tested across runtime restart.

### Manual pairing
A manual-code button with no available PairingOffer is not functional. The real UI must have a truthful way to acquire/input the receiver offer identity needed for manual pairing.

### QR camera ownership
A logical PairingCameraOwnership actor alone does not stop the existing production camera. Scanner presentation/start must be coordinated with the actual capture camera lifecycle.

### TLS pinning evidence
Do not leave mandatory network security tests skipped only because an external `openssl` executable is absent. Make deterministic pinned-TLS tests runnable in the normal locked test environment.

### Swift protocol authority
Swift and Python must actually consume the same golden protocol fixture/derived source, not maintain two independently typed copies that merely look similar.

### Completion identity
Production Swift must validate transfer ID + package digest + authenticated + verified + terminal state before success.

### End-to-end evidence
Static source-string inspection is not cross-language integration. Create executable behavior evidence over the actual receiver boundary and the same production transport contract.

## Ordered children

Execute exactly these nine children in order:

### 1. PL-0119 — Canonical production finalization and complete failure matrix

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CODEX_LOG_V03.md

Preserve useful V02 code, close the V03 gaps, add production-behavior evidence, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 2. PL-0121 — One authoritative Swift/Python golden Transfer Protocol contract

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CODEX_LOG_V03.md

Preserve useful V02 code, close the V03 gaps, add production-behavior evidence, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 3. PL-0122 — Functional manual/QR pairing with real capture-camera ownership

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CODEX_LOG_V03.md

Preserve useful V02 code, close the V03 gaps, add production-behavior evidence, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 4. PL-0123 — Executable pinned TLS/auth boundary without OpenSSL dependency

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CODEX_LOG_V03.md

Preserve useful V02 code, close the V03 gaps, add production-behavior evidence, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 5. PL-0124 — Persisted same-transfer sender resume across retry/app restart

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CODEX_LOG_V03.md

Preserve useful V02 code, close the V03 gaps, add production-behavior evidence, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 6. PL-0125 — Swift production completion identity/state hardening

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_LOG_V03.md

Preserve useful V02 code, close the V03 gaps, add production-behavior evidence, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 7. PL-0126 — Production transfer UI same-ID retry/cancel/failure test closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_LOG_V03.md

Preserve useful V02 code, close the V03 gaps, add production-behavior evidence, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 8. PL-0132 — Complete manual/network mask/diagnostics report matrix

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CODEX_LOG_V03.md

Preserve useful V02 code, close the V03 gaps, add production-behavior evidence, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 9. PL-0134 — Executable cross-language sender-to-receiver-to-ingest harness

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_LOG_V03.md

Preserve useful V02 code, close the V03 gaps, add production-behavior evidence, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

## Gate A — finalization + wire authority after PL-0121

Prove:
- actual production finalization uses CanonicalFinalizationSource;
- complete failure/rollback matrix;
- one shared V1 golden contract consumed by Python and Swift;
- unsupported-version decoding fails closed in both languages.

## Gate B — functional iPhone pairing/security after PL-0123

Prove:
- manual pairing can actually be completed from the real Send-to-PackLab workflow;
- QR scanning is refused until the production camera releases ownership;
- production capture and QR scanner cannot run concurrently;
- production camera ownership is restored after QR finish/cancel/failure;
- real HTTPS pairing/auth works with pinned receiver identity;
- wrong pin, replay, expiry, wrong receiver and missing auth fail over the network boundary;
- tests run without an external OpenSSL executable dependency.

## Gate C — same-ID transfer after PL-0126

Prove:
- first transfer ID is persisted;
- cancel preserves resumability;
- retry queries receiver status;
- retry uses the same transfer ID;
- runtime/app restart restores sender identity and same ID;
- transfer resumes at authoritative receiver offset;
- no duplicate transfer is created;
- completion requires matching transfer ID/digest/auth/verified/terminal state;
- SwiftUI reflects actual network behavior and all phases truthfully.

## Gate D — final evidence after PL-0134

Prove:
- separate manual and network reports;
- mask present/absent, diagnostics present/absent, calibration present/absent;
- executable sender→HTTPS receiver→resume→verify→ingest chain;
- exactly-once raw/index/report;
- corrupt/bad/checksum/future/unsafe/missing-image invalid inputs never reach raw authority.

## Execution discipline

For every child:
1. read TASKS.md, this master prompt/criteria, V03 child prompt/criteria and V02 audit;
2. inspect current `main`;
3. preserve all already accepted M05 behavior;
4. implement only the authorized gap;
5. add production-seam tests;
6. run focused tests;
7. run full locked suite;
8. run relevant iOS project/static and Python Ruff/compileall checks;
9. run `git diff --check`;
10. verify protected files untouched;
11. run secrets/private-key/signing/cache review;
12. create one implementation/evidence commit;
13. publish one separate V03 child log-only commit;
14. verify remote visibility before the next child.

## STOP conditions

Stop if:
- authorization/repository safety fails;
- fix requires M06/later milestone implementation;
- a genuine owner/ADR decision is required;
- security would need weakening/bypass;
- private keys/credentials would enter Git;
- protected files require Codex edits;
- locked tests cannot run truthfully;
- physical/native evidence would need fabrication.

On stop, publish truthful evidence and end the master log `BATCH_STOPPED`.

## Final validation

After all nine:
- all 7 already accepted M05 children remain green;
- M03/M04 remain accepted;
- PL-0068 remains OWNER_REQUIRED;
- no M06 implementation;
- full locked suite passes;
- no mandatory security/integration test remains skipped merely because external OpenSSL is absent;
- relevant Swift/project/static checks pass;
- Ruff/compileall pass;
- `git diff --check` passes;
- TASKS.md/ChatGPT audits untouched;
- privacy/secrets/signing review clean;
- every child has distinct implementation/evidence + log-only commits.

Native physical iPhone/AirDrop/real-LAN may remain unexecuted and must not be falsely claimed. The required deterministic production-contract tests must still run.

## User-facing link policy

Every user-facing repository reference must be a full GitHub URL. Never output local filesystem paths.

## Final handoff

Publish:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_LOG_V02.md

Index all nine children with full GitHub prompt/criteria/audit/log links, exact implementation/log commits, test results, security evidence and limitations.

End exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not self-audit.
