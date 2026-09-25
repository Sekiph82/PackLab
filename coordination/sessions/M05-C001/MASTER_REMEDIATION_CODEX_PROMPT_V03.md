# M05-BATCH-004 — Master Remediation Codex Work Order V03

Milestone: **M05 — Transfer & Ingest**
Purpose: **Close the final six M05 audit findings**
Authorized tasks: **PL-0119, PL-0121, PL-0122, PL-0125, PL-0126, PL-0134**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Previous master audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_V02.md
This master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Master criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V03.md
Required master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_LOG_V03.md

## Authorization gate

TASKS.md must show:
- Current Milestone: M05
- Current Sprint: M05-BATCH-004
- Current Task: M05-BATCH-004
- Current Task Status: READY
- Required Actor: CODEX
- exactly 10 M05 children checked/accepted
- exactly these six M05 children unchecked: PL-0119, PL-0121, PL-0122, PL-0125, PL-0126, PL-0134
- M03/M04 accepted
- PL-0068 unchecked / OWNER_REQUIRED
- M06 not started
- Next Task/Action pointing to this master prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Fast-forward only if safe. Never reset, rebase, force-push, destructively clean or stash owner work.

Never edit TASKS.md or ChatGPT audit artifacts. Never start M06. Never fabricate PL-0068 evidence.

## Preserve accepted M05 architecture

Do not regress:
- real finalized Scan History Share/Send UI;
- HTTPS receiver/pairing/auth boundary;
- same-transfer sender ID persistence/resume;
- manual ingest/common validation;
- quarantine/raw/index/report authorities;
- M03/M04 accepted behavior.

This batch is a surgical evidence/integration closure.

## Ordered children

### 1. PL-0119 — Wire canonical finalization into real app export flow

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CODEX_LOG_V04.md

Execute only the frozen V04 remediation, preserve all accepted M05 architecture, add production-seam evidence, create one implementation/evidence commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 2. PL-0121 — Fix Swift negative decoder matrix for all V1 wire models

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CODEX_LOG_V04.md

Execute only the frozen V04 remediation, preserve all accepted M05 architecture, add production-seam evidence, create one implementation/evidence commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 3. PL-0122 — Pairing lifecycle already-idle and wrong-version closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CODEX_LOG_V04.md

Execute only the frozen V04 remediation, preserve all accepted M05 architecture, add production-seam evidence, create one implementation/evidence commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 4. PL-0125 — Complete production Swift completion failure matrix

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_LOG_V04.md

Execute only the frozen V04 remediation, preserve all accepted M05 architecture, add production-seam evidence, create one implementation/evidence commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 5. PL-0126 — Complete transfer UI/service failure and restore matrix

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_LOG_V04.md

Execute only the frozen V04 remediation, preserve all accepted M05 architecture, add production-seam evidence, create one implementation/evidence commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 6. PL-0134 — Persisted sender-state executable harness closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_LOG_V04.md

Execute only the frozen V04 remediation, preserve all accepted M05 architecture, add production-seam evidence, create one implementation/evidence commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

## Gate A — real finalization authority

The app must have an actual production route:
accepted active session
→ canonical accepted records/immutable bytes
→ canonical finalization source
→ finalized .packscan
→ exported history
→ Share/Send eligibility.

A canonical helper that no production code calls is not sufficient.

## Gate B — protocol/pairing correctness

Prove:
- Swift negative decoding uses each correct wire model;
- unsupported protocol/version fails closed across status/control/completion/error;
- manual pairing remains functional;
- QR pairing succeeds when production camera is already safely idle/released;
- QR pairing fails when active production camera cannot release;
- production camera is restored only when pairing displaced it;
- wrong-version PairingOffer is tested.

## Gate C — sender completion/UI failure matrix

Prove through production Swift seams:
- wrong transfer ID rejected;
- wrong digest rejected;
- unauthenticated ack rejected;
- unverified ack rejected;
- non-terminal ack rejected;
- corrupted/wrong-declared digest remains retryable;
- sender identity is retained on failure;
- network cancel preserves source/resume identity;
- same-ID status/retry remains authoritative;
- checksum retryable failure and terminal failure are visually distinct;
- fresh runtime restore derives UI phase/progress from persisted identity + receiver status;
- verified matching terminal completion alone clears identity.

## Gate D — executable cross-language harness

The Python/transport harness must genuinely:
- persist sender identity;
- destroy first sender;
- create a fresh sender;
- read/validate persisted transfer ID/digest/receiver identity;
- derive resumed requests from restored state;
- verify pairing-offer certificate fingerprint against the live certificate;
- apply the same completion gate as Swift;
- continue partial transfer after receiver restart;
- cancel/resume;
- finish verified;
- import exactly once to raw/index/report.

Hard-coded transfer IDs after “restart” are not acceptable evidence.

## Per-child discipline

For every child:
1. read TASKS.md, master prompt/criteria, V04 child prompt/criteria and V03 audit;
2. inspect final current `main`;
3. implement only the frozen remaining gap;
4. add production-seam tests;
5. run focused tests;
6. run full locked suite;
7. run relevant Swift/project/static and Python Ruff/compileall checks;
8. run `git diff --check`;
9. prove TASKS.md/ChatGPT audits untouched;
10. review secrets/private keys/signing/caches;
11. create one implementation/evidence commit;
12. publish the V04 child log in a separate log-only commit;
13. verify remote visibility before continuing.

## STOP conditions

Stop if:
- authorization/repository safety fails;
- the fix requires M06/later milestone implementation;
- a genuine owner/ADR decision is required;
- security would need weakening/bypass;
- private keys/credentials would enter Git;
- protected files require Codex edits;
- locked tests cannot run truthfully;
- physical/native evidence would need fabrication.

On STOP publish truthful evidence and end master log `BATCH_STOPPED`.

## Final validation

After all six:
- all 10 already accepted M05 children remain green;
- M03/M04 remain accepted;
- PL-0068 remains OWNER_REQUIRED;
- no M06 implementation;
- full locked suite passes;
- deterministic TLS/transport tests run without external OpenSSL dependence;
- relevant Swift/project/static checks pass;
- Ruff/compileall pass;
- `git diff --check` passes;
- TASKS.md/ChatGPT audits untouched;
- privacy/secrets/signing review clean;
- every child has distinct implementation/evidence + log-only commits.

Native physical iPhone/AirDrop/real-LAN may remain unexecuted and must not be falsely claimed.

## User-facing link policy

Every user-facing repository reference must be a full GitHub URL. Never output local filesystem paths.

## Final handoff

Publish:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_LOG_V03.md

Index all six children with full GitHub prompt/criteria/audit/log links, exact implementation/log commits, test results and limitations.

End exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not self-audit.
