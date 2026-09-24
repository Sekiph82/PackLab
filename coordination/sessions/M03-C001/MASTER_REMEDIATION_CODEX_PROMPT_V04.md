# M03-BATCH-005 — Master Remediation Codex Work Order V04

Milestone: **M03 — iOS Capture Foundation**
Purpose: **Close the 16 remaining Batch-004 audit findings**
Authorized tasks: **PL-0071, PL-0073, PL-0074, PL-0075, PL-0076, PL-0077, PL-0079, PL-0080, PL-0081, PL-0084, PL-0085, PL-0088, PL-0089, PL-0090, PL-0092, PL-0093**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Previous master audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_V03.md
This master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V04.md
Master criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V04.md
Required master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_LOG_V04.md

## Authorization gate

TASKS.md must show:
- Current Milestone: M03
- Current Task: M03-BATCH-005
- Current Task Status: READY
- Required Actor: CODEX
- accepted M03 children remain checked
- PL-0068 remains unchecked / OWNER_REQUIRED
- Next Task/Action points to this master V04 prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Fast-forward only when safe. Never reset, rebase, force-push, destructively clean or stash owner work.

Never edit root TASKS.md or any ChatGPT audit artifact. Never start M04. Never fabricate PL-0068 evidence.

## Accepted M03 children that must not regress

Already independently accepted:
- PL-0069
- PL-0070
- PL-0072
- PL-0078
- PL-0082
- PL-0083
- PL-0086
- PL-0087
- PL-0091

Do not rewrite these for convenience. Touch their shared code only when required by an authorized V05 remediation, and prove no regression.

## Batch objective

Batch-004 solved most product architecture. Batch-005 is deliberately narrow. It must close only the final 16 gaps:
- Apple-framework adapters need missing integrated tests/composition;
- camera controls/recovery must be bound to the live runtime;
- encoded photo JSON must be validated against the authoritative schema;
- accepted pose/motion evidence must enter real persisted capture records;
- AR owner/reset and overlay runtime need direct injected-owner/runtime evidence;
- storage/gallery/resume need complete failure matrices;
- history/deletion need the remaining authoritative/failure cases.

Do not create new parallel helpers when an existing production seam can be wired/tested.

## Ordered children

Execute exactly these 16 children in order:

### 1. PL-0071 — Still adapter cancellation/test closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 2. PL-0073 — Focus production-runtime composition closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 3. PL-0074 — Exposure production-runtime/metadata closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 4. PL-0075 — White-balance production-runtime/metadata closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 5. PL-0076 — Encoded photo-schema validation closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 6. PL-0077 — Unified recovery-owner composition closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 7. PL-0079 — AR physical-owner behavior-test closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 8. PL-0080 — Accepted-still pose persistence closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 9. PL-0081 — Motion accepted-persistence closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 10. PL-0084 — AR reset owner-test closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 11. PL-0085 — Live overlay value-propagation closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 12. PL-0088 — All-stage crash transaction evidence closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 13. PL-0089 — Gallery mutation evidence closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 14. PL-0090 — Resume/discard failure-matrix closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 15. PL-0092 — History state-contract/test closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 16. PL-0093 — Deletion missing/history-failure evidence closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CODEX_LOG_V05.md

Execute only the frozen V05 remediation, preserve all already accepted M03 behavior, create a distinct implementation commit and then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

## User-facing link policy

Codex may work with local checkout paths internally, but **every user-facing link** in progress messages, child handoffs and the final handoff must be a full GitHub URL.

Never show:
- `C:\Users\...`
- `C:/Users/...`
- `file://...`
- Markdown hyperlinks whose target is a local path.

For repository artifacts use canonical URLs such as:
`https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_LOG_V04.md`

Before handoff verify every linked artifact is remotely visible on `main`.

## Per-child discipline

For every child:
1. read TASKS.md, this master prompt/criteria, the V05 child prompt/criteria and previous V04 audit;
2. inspect current `main`, including earlier Batch-005 child changes;
3. implement only the remaining finding;
4. add behavior-bearing tests at the production-used seam;
5. run focused tests and relevant M03 regression/project/static validation available on the host;
6. run `git diff --check` and verify TASKS.md/ChatGPT audits are untouched;
7. review secrets/signing/private/caches;
8. create a distinct implementation commit;
9. publish the V05 child log in a separate commit;
10. verify remote visibility and continue only when green.

## STOP conditions

Stop the batch if:
- authorization/repository safety fails;
- a finding requires M04 or a genuine owner/ADR decision;
- protected files would need Codex edits;
- a privacy/signing risk appears;
- a mandatory regression cannot be repaired within the child.

On STOP publish truthful evidence and end the master log `BATCH_STOPPED`.

## Final validation

After all 16:
- verify all 9 previously accepted M03 children remain unregressed;
- verify PL-0068 remains OWNER_REQUIRED;
- verify no M04 work;
- run full repository-supported M03 regression and project/static checks;
- run `git diff --check`;
- verify protected files untouched;
- inspect privacy/signing/cache scope;
- verify distinct implementation/log commits for all 16 children.

Publish:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_LOG_V04.md

The master log must index all 16 children with full GitHub prompt/criteria/audit/log links, start commit, implementation commit, log commit, validation and limitations.

The **final user-facing handoff must provide the full GitHub URL** to the master log, never a local path.

End the master log exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not self-audit.
