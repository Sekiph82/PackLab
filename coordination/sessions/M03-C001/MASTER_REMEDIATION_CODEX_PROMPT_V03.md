# M03-BATCH-004 — Master Remediation Codex Work Order V03

Milestone: **M03 — iOS Capture Foundation**
Purpose: **Close the final Batch-003 independent-audit findings**
Tasks: **PL-0069, PL-0071 through PL-0093** (24 tasks)
Accepted/excluded child: **PL-0070**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Previous master audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_V02.md
This master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Master criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V03.md
Required master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_LOG_V03.md

## Authorization gate

TASKS.md must show:
- Current Milestone: M03
- Current Task: M03-BATCH-004
- Current Task Status: READY
- Required Actor: CODEX
- PL-0070 already accepted
- PL-0068 still unchecked / OWNER_REQUIRED
- Next Task/Action pointing to this master V03 prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Fast-forward only when safe. Never reset/rebase/force-push/destructively clean/stash owner work.

Never edit root TASKS.md or ChatGPT audit files. Never start M04. Never fabricate PL-0068 physical evidence.

## Batch-004 strategy

Batch-003 already added most production structures. This pass must **not** build new parallel helpers. It must close the last gaps by:
- wiring existing adapters/services into actual runtime composition;
- adding injected drivers used by production code so Apple-specific behavior is testable without physical hardware;
- cross-validating wire constants against authoritative schemas;
- making persistence/finalization/destructive operations genuinely crash/failure safe;
- testing the real production seam instead of a nearby pure struct.

Native Xcode/iPhone execution is optional only insofar as the Windows host cannot perform it; lack of Apple execution does not waive source-level injected/conditional test evidence.

## Ordered children

Execute exactly this order:

### 1. PL-0069 — Preview bridge behavior-test closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_PROMPT_V05.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CHATGPT_AUDIT_CRITERIA_V05.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CHATGPT_AUDIT_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_LOG_V05.md

Production preview code is largely correct; close the real controller/driver behavior-test gap for authorization, start failure and repeated lifecycle.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 2. PL-0071 — Still adapter composition/test closure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CODEX_LOG_V04.md

Compose NextLevelStillCaptureAdapter with deterministic selected main-wide/session ownership and test the actual delegate adapter exact-once boundary.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 3. PL-0072 — Valid image metadata fixture/integration

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CODEX_LOG_V04.md

Route originals through ImageIO extraction in production and prove valid JPEG/HEIF metadata, dimensions, immutability and derivative separation.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 4. PL-0073 — Focus runtime binding

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CODEX_LOG_V04.md

Connect selected-device focus adapter to visible runtime state and test real stabilization/lock/wrong-device behavior.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 5. PL-0074 — Exposure runtime/metadata binding

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CODEX_LOG_V04.md

Connect exposure state/readings to runtime UI and accepted-photo metadata persistence using the selected coordinator.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 6. PL-0075 — White-balance runtime/metadata binding

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CODEX_LOG_V04.md

Connect stable observed white balance to runtime UI and persisted accepted-photo metadata.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 7. PL-0076 — Authoritative photo-schema invariants

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_LOG_V04.md

Cross-validate against M02 schema and close status/value/source/numeric invariants, especially ISO.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 8. PL-0077 — Recovery production composition

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CODEX_LOG_V04.md

Wire recovery owner to actual UI, in-flight still cancellation and bounded real session restart with integrated tests.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 9. PL-0078 — Health gate physical enforcement

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CODEX_LOG_V04.md

Put the live health admission gate directly in the real still-capture call path and prove hard-stop prevents capturePhoto.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 10. PL-0079 — AR physical-owner lifecycle evidence

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CODEX_LOG_V04.md

Keep one SharedARSessionOwner and test its lifecycle/capability/interruption behavior through an injected production-used session driver.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 11. PL-0080 — Accepted-still pose persistence

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CODEX_LOG_V04.md

Bind and persist pose evidence from the actual accepted still with correct monotonic timestamp semantics.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 12. PL-0081 — Single MotionService accepted binding

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_LOG_V04.md

Eliminate second physical motion ownership and persist accepted-still motion binding.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 13. PL-0082 — Pose schema cross-check

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CODEX_LOG_V04.md

Cross-check coordinate/basis/unit constants against an authoritative fixture derived from pose.schema.json.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 14. PL-0083 — Tracking runtime integration tests

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CODEX_LOG_V04.md

Test live hysteresis/diagnostics through injected CaptureRuntimeViewModel services rather than only policy structs.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 15. PL-0084 — AR reset lifecycle tests

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_LOG_V04.md

Test real owner reset/recovery/failure/degradation/interruption epochs using an injected session driver.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 16. PL-0085 — Live overlay runtime tests

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CODEX_LOG_V04.md

Prove runtime pose/motion/epoch values change over time and stop cleanly.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 17. PL-0086 — Diagnostics privacy/limit evidence

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CODEX_LOG_V04.md

Add realistic privacy redaction and exact maximum-record boundary tests.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 18. PL-0087 — New Scan exact callback

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CODEX_LOG_V04.md

Prove real Start/Cancel callback semantics and preserve the session-creation handoff.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 19. PL-0088 — Crash transaction recovery

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_LOG_V04.md

Make source+record+state transaction recover atomically at every crash stage.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 20. PL-0089 — Atomic gallery mutation

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_LOG_V04.md

Wire Retake UI to execution and make delete/retake state/files/audit transactional.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 21. PL-0090 — Resume recovery evidence

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CODEX_LOG_V04.md

Test actual discovery/reopen/resume/discard across partial transaction and corruption cases.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 22. PL-0091 — Atomic package/finalization publication

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CODEX_LOG_V04.md

Make package and finalization record publication one rollback-safe operation.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 23. PL-0092 — Authoritative history validation

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CODEX_LOG_V04.md

Validate finalization record identity/state/package existence and test real state transitions/multi-session ordering.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 24. PL-0093 — Deletion failure semantics/symlink

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CHATGPT_AUDIT_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CODEX_LOG_V04.md

Make all deletion APIs fail on partial failure and add real symlink/destructive-boundary tests.

Preserve all correct Batch-003 behavior. Implement only the remaining frozen gap, test the actual production-used seam or authoritative persistence contract, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

## Integration gates

### Camera gate after PL-0078
Prove one production camera path:
preview authorization/lifecycle → deterministic main-wide selection → real still adapter → immutable source/ImageIO metadata → focus/exposure/WB visible state → schema-valid photo metadata → recovery owner → live health gate → actual capture admission.

### Tracking gate after PL-0086
Prove one evidence path:
SharedARSessionOwner + one MotionService → accepted still timestamp → pose/motion binding → authoritative coordinate contract → tracking hysteresis/reset epochs → live runtime overlay → versioned private-safe diagnostics.

### Session gate after PL-0093
Prove one persisted path:
New Scan → crash-atomic accepted capture → transactional gallery mutations → authoritative resume/discard → rollback-safe PackScan finalization → authoritative history → safe deletion with non-silent partial failures.

## Per-child discipline

For every child:
1. read current TASKS, master prompt/criteria, child prompt/criteria and previous audit;
2. inspect final main, including prior Batch-004 child changes;
3. implement only the remaining finding;
4. add behavior-bearing tests against the production-used seam;
5. run all available focused/relevant regression and static/project checks;
6. verify git diff --check and protected TASKS/audit files;
7. commit implementation;
8. publish child log in a separate commit;
9. verify remote visibility;
10. continue only when validation-green.

## STOP conditions

Stop the batch if:
- authorization/repository safety fails;
- a frozen finding requires M04 or a new owner/ADR decision;
- privacy/signing risk appears;
- Codex would need to edit TASKS/audits;
- a mandatory regression cannot be repaired inside the child.

On STOP publish truthful evidence and master log ending `BATCH_STOPPED`.

## Final validation

After all 24:
- verify PL-0070 remains unregressed;
- verify PL-0068 remains OWNER_REQUIRED;
- verify no M04 work;
- run full repository-supported M03 regression and project/static checks;
- run git diff --check;
- verify no protected-file edits;
- review privacy/signing/cache scope;
- verify distinct implementation/log commits for every child.

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_LOG_V03.md indexing every child with prompt, criteria, previous audit, start, implementation, log, validation and limitations.

End exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not self-audit.
