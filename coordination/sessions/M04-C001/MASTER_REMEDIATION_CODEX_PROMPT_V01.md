# M04-BATCH-002 — Master Remediation Codex Work Order V01

Milestone: **M04 — Guided Capture & Quality Intelligence**
Purpose: **Remediate the 24 failed children from M04-BATCH-001**
Authorized tasks: **PL-0094–PL-0110 and PL-0112–PL-0118**
Accepted/excluded child: **PL-0111**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Canonical tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
Previous master audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CHATGPT_AUDIT_V01.md
This master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Master criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V01.md
Required master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_LOG_V01.md

## Authorization gate

Before material work, TASKS.md must show:
- Current Milestone: M04
- Current Task: M04-BATCH-002
- Current Task Status: READY
- Required Actor: CODEX
- PL-0111 checked/accepted
- PL-0068 still unchecked / OWNER_REQUIRED
- M03 still accepted
- Next Task/Action pointing to this master remediation prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Before work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Fast-forward only if safe. Never reset, rebase, force-push, destructively clean or stash owner work.

Never edit root TASKS.md or ChatGPT audit artifacts. Never start M05. Never fabricate PL-0068 physical evidence.

## Remediation architecture

M04-BATCH-001 created strong deterministic models but left most of them disconnected from the real app.

Batch-002 must converge on **one production M04 runtime/coordinator** that extends the already accepted M03 architecture:

live candidate image/luminance + existing MotionService + existing pose/session state
→ sharpness / motion blur / highlight / shadow / framing / background
→ authoritative QualityDecision
→ every-candidate QualityCandidateLog
→ accepted-pose coverage / duplicate gate
→ auto or manual capture through the existing health-gated still-capture service
→ immutable accepted-capture transaction
→ coverage/detail/completion state
→ live SwiftUI guidance
→ persisted M04 session context.

Do **not** create:
- another camera owner;
- another AR session;
- another CoreMotion manager;
- another still-capture path;
- preset-specific duplicate quality engines.

The production runtime must consume the versioned preset selected in New Scan.

## Known correctness defects to close

The child prompts are authoritative; at minimum Batch-002 must close these known issues:
- fix literal reason-code interpolation in sharpness/motion;
- use clipping `warningFraction` meaningfully;
- enforce `rejectUnavailableClipping`;
- stop hard-coding camera/session/storage readiness in New Scan preflight;
- make accepted pose binding authoritative for coverage;
- make auto/manual capture use the existing production capture/session transaction;
- wire coverage/completion/protocol UI into the real app;
- persist transparent treatment, asymmetric policy and turntable evidence.

## Test environment gate

The previous batch could not collect the full suite because the locked environment lacked `jsonschema`.

Batch-002 must inspect the repository dependency contract and make the **declared locked test environment** capable of collecting/running the authoritative tests. If `jsonschema` is required by tracked tests, add/pin it in the appropriate dev/test dependency definition and lockfile as a justified adjacent build/test change.

Do not:
- pip-install an untracked workaround;
- skip the authoritative schema tests;
- claim a green full suite if collection still fails.

If dependency repair is impossible without a broader owner/ADR decision, stop the batch truthfully.

## Ordered children

Execute exactly these 24 tasks in order:

### 1. PL-0094 — Sharpness runtime + reason-code closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0094_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0094_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0094_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0094_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 2. PL-0095 — Motion-blur runtime + reason-code closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0095_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0095_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0095_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0095_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 3. PL-0096 — Highlight clipping threshold/runtime closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0096_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0096_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0096_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0096_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 4. PL-0097 — Shadow clipping threshold/runtime closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0097_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0097_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0097_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0097_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 5. PL-0098 — Framing live UI/logging closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0098_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0098_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0098_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0098_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 6. PL-0099 — Background complexity live warning closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0099_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0099_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0099_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0099_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 7. PL-0100 — Authoritative quality-decision closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0100_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0100_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0100_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0100_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 8. PL-0101 — Every-candidate quality logging closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 9. PL-0102 — Authoritative accepted-pose coverage closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0102_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0102_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0102_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0102_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 10. PL-0103 — Live coverage UI closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0103_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0103_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0103_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0103_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 11. PL-0104 — Production auto-capture closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 12. PL-0105 — Production duplicate gate closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0105_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0105_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0105_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0105_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 13. PL-0106 — Bottle-ring live guidance closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 14. PL-0107 — Detail-pass production integration closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 15. PL-0108 — Base-pass production integration closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0108_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0108_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0108_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0108_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 16. PL-0109 — Completion persistence/live guidance closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 17. PL-0110 — Manual-capture production closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0110_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0110_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0110_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0110_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 18. PL-0112 — Glossy/PET live policy/guidance closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0112_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0112_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0112_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0112_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 19. PL-0113 — Transparent treatment workflow closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0113_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0113_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0113_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0113_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 20. PL-0114 — Asymmetric/Jerrycan policy persistence closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0114_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0114_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0114_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0114_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 21. PL-0115 — Closure/Cap production mode closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0115_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0115_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0115_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0115_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 22. PL-0116 — Turntable capture/evidence closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0116_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0116_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0116_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0116_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 23. PL-0117 — Capture Protocol navigation closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0117_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0117_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0117_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0117_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 24. PL-0118 — Authoritative preflight readiness closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0118_CODEX_PROMPT_V02.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0118_CHATGPT_AUDIT_CRITERIA_V02.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0118_CHATGPT_AUDIT_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0118_CODEX_LOG_V02.md

Read the frozen V02 child prompt/criteria and previous audit. Preserve all valid V01 work, close only the audited defects/integration gaps, add production-seam tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

## Integration gate after PL-0101 — production quality runtime

Prove:
- one candidate input enters all six metrics;
- active preset thresholds are used;
- raw metrics/stable reason codes are available live;
- QualityDecision is authoritative;
- every candidate, accepted or rejected, is logged;
- unavailable evidence is explicit;
- hard-reject policy switches actually work.

## Integration gate after PL-0110 — guided capture runtime

Prove:
- accepted PoseCaptureBinding drives coverage;
- live coverage UI updates after accepted captures;
- duplicate gate participates before capture acceptance;
- GuidedAutoCaptureService uses the existing health-gated still service;
- accepted auto/manual captures use the canonical session transaction;
- ring/detail/base/completion guidance is live and persisted;
- manual override cannot bypass hard safety/integrity gates.

## Integration gate after PL-0118 — preset/protocol/preflight workflow

Prove:
- New Scan selected preset drives real quality + coverage policy;
- CaptureProtocolView is in the actual navigation flow;
- transparent treatment selection is persisted;
- asymmetric and turntable policies are persisted and used;
- real runtime camera/session/storage/health readiness drives preflight;
- PL-0068 remains ownerRequired warning, never fabricated verification.

## Per-child discipline

For every child:
1. read TASKS.md, master prompt/criteria, V02 child prompt/criteria and V01 audit;
2. inspect current `main`, including earlier Batch-002 integration changes;
3. implement only the authorized remediation;
4. add behavior-bearing tests at production-used seams;
5. run focused + relevant regression/project/static checks;
6. run `git diff --check`;
7. prove TASKS.md / ChatGPT audits untouched;
8. review secrets/signing/private/caches;
9. create a distinct implementation commit;
10. publish the child V02 log in a separate log-only commit;
11. verify remote visibility before continuing.

## STOP conditions

Stop if:
- authorization/repository safety fails;
- a required fix needs M05 or later-milestone implementation;
- a genuine owner/ADR decision is required;
- physical evidence would need fabrication;
- protected files would need Codex edits;
- privacy/signing risk appears;
- the full declared test environment cannot be made collectible without an out-of-scope change.

On stop, publish truthful child/master evidence and end master log `BATCH_STOPPED`.

## Final validation

After all 24:
- PL-0111 remains unregressed;
- M03 remains accepted;
- PL-0068 remains OWNER_REQUIRED;
- no M05 work;
- full declared Python suite collects and runs, including authoritative schema tests;
- all available M04 static/project checks pass;
- `git diff --check` passes;
- TASKS.md/ChatGPT audits untouched;
- privacy/signing/cache review clean;
- each child has distinct implementation and log commits.

Native Swift/Xcode/iPhone results may be claimed only if actually executed. Windows source/static evidence is not physical validation.

## User-facing link policy

Every user-facing repository link must be a full GitHub URL. Never show local checkout/file links.

## Final handoff

Publish:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_LOG_V01.md

The master log must index all 24 children with full GitHub prompt/criteria/audit/log links, implementation/log commits, validation results and limitations.

End exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not self-audit.
