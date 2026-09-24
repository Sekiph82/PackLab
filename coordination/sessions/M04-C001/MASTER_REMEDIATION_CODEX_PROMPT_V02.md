# M04-BATCH-003 — Master Remediation Codex Work Order V02

Milestone: **M04 — Guided Capture & Quality Intelligence**
Purpose: **Close the final nine M04 audit findings**
Authorized tasks: **PL-0094, PL-0101, PL-0102, PL-0104, PL-0105, PL-0106, PL-0107, PL-0108, PL-0109**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Previous master audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_V02.md
This master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Master criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V02.md
Required master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_LOG_V02.md

## Authorization gate

TASKS.md must show:
- Current Milestone: M04
- Current Task: M04-BATCH-003
- Current Task Status: READY
- Required Actor: CODEX
- 16 M04 children already accepted
- exactly these 9 children still unchecked
- M03 accepted
- PL-0068 unchecked / OWNER_REQUIRED
- Next Task/Action pointing to this master V02 prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Fast-forward only when safe. Never reset, rebase, force-push, destructively clean or stash owner work.

Never edit root TASKS.md or ChatGPT audit artifacts. Never start M05. Never fabricate PL-0068 evidence.

## Preserve the current architecture

Batch-002 successfully integrated the production M04 runtime. This final pass is **not** an architecture rewrite.

Preserve:
- one M03 camera owner;
- one ARTrackingService owner;
- one MotionService owner;
- one health-gated still-capture service;
- one M04 candidate quality runtime;
- one authoritative QualityDecision path;
- one candidate log store;
- one active OrbitCoverageModel;
- one canonical accepted-capture transaction;
- the existing live coverage/completion/protocol/preflight UI;
- all 16 accepted M04 children.

The remaining work is narrow: missing boundary/failure tests plus one explicit base-pass `skipped` state.

## Ordered children

### 1. PL-0094 — Sharpness frame/boundary evidence closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0094_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0094_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0094_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0094_CODEX_LOG_V03.md

Execute only the frozen V03 remediation, preserve the integrated M04 runtime, add production-seam evidence, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 2. PL-0101 — Corrupt quality-log fail-closed closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CODEX_LOG_V03.md

Execute only the frozen V03 remediation, preserve the integrated M04 runtime, add production-seam evidence, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 3. PL-0102 — Orbit elevation-boundary evidence closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0102_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0102_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0102_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0102_CODEX_LOG_V03.md

Execute only the frozen V03 remediation, preserve the integrated M04 runtime, add production-seam evidence, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 4. PL-0104 — Auto-capture gate-matrix closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CODEX_LOG_V03.md

Execute only the frozen V03 remediation, preserve the integrated M04 runtime, add production-seam evidence, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 5. PL-0105 — Duplicate threshold-boundary closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0105_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0105_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0105_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0105_CODEX_LOG_V03.md

Execute only the frozen V03 remediation, preserve the integrated M04 runtime, add production-seam evidence, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 6. PL-0106 — Ring boundary evidence closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CODEX_LOG_V03.md

Execute only the frozen V03 remediation, preserve the integrated M04 runtime, add production-seam evidence, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 7. PL-0107 — Detail-pass framing-boundary closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CODEX_LOG_V03.md

Execute only the frozen V03 remediation, preserve the integrated M04 runtime, add production-seam evidence, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 8. PL-0108 — Base-pass skipped-state and rejection closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0108_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0108_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0108_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0108_CODEX_LOG_V03.md

Execute only the frozen V03 remediation, preserve the integrated M04 runtime, add production-seam evidence, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 9. PL-0109 — Completion mixed-pass/resume closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CHATGPT_AUDIT_CRITERIA_V03.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CHATGPT_AUDIT_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CODEX_LOG_V03.md

Execute only the frozen V03 remediation, preserve the integrated M04 runtime, add production-seam evidence, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

## Integration expectations

### Quality evidence
- Sharpness WARN/REJECT and exact analyzer boundaries are proven with deterministic fixtures.
- Corrupt quality-log reopen fails closed and leaves canonical session state untouched.

### Coverage and auto-capture evidence
- Orbit/ring elevation and sector boundaries are deterministic.
- Auto-capture gate matrix proves every blocked condition suppresses backend invocation.
- Duplicate translation/elevation/signature thresholds are proven exactly.

### Detail/base/completion evidence
- Detail framing minimum boundary is proven.
- Base pass distinguishes unavailable, skipped, incomplete and complete.
- Quality-rejected base candidate does not persist accepted evidence.
- Completion diagnostics handle mixed required detail passes and restore correctly into a fresh runtime.

## Per-child discipline

For each child:
1. read TASKS.md, this master prompt/criteria, V03 child prompt/criteria and V02 audit;
2. inspect current `main`;
3. implement only the frozen remaining gap;
4. add production-seam behavior tests;
5. run focused tests;
6. run full declared locked suite;
7. run relevant static/project checks;
8. run `git diff --check`;
9. verify TASKS.md/ChatGPT audits untouched;
10. review privacy/signing/secrets/caches;
11. create one implementation commit;
12. publish child log in a separate log-only commit;
13. verify remote visibility before continuing.

## STOP conditions

Stop the batch if:
- authorization/repository safety fails;
- a required fix needs M05/later milestone work;
- a genuine owner/ADR decision is required;
- physical evidence would need fabrication;
- protected files would need edits;
- privacy/signing risk appears;
- full declared test environment cannot run truthfully.

On STOP publish truthful evidence and end the master log `BATCH_STOPPED`.

## Final validation

After all 9:
- all 16 previously accepted M04 children remain unregressed;
- M03 remains accepted;
- PL-0068 remains OWNER_REQUIRED;
- no M05 work;
- full declared locked suite passes;
- relevant project/static checks pass;
- `git diff --check` passes;
- TASKS.md/ChatGPT audits untouched;
- privacy/signing/cache review clean;
- every child has distinct implementation + log-only commits.

Native Swift/Xcode/iPhone results may be claimed only if actually executed.

## User-facing link policy

Every user-facing repository reference must be a full GitHub URL. Never output local checkout/file links.

## Final handoff

Publish:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_LOG_V02.md

The master log must index all 9 children with full GitHub prompt/criteria/audit/log links, implementation/log commits, validation results and limitations.

End exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not self-audit.
