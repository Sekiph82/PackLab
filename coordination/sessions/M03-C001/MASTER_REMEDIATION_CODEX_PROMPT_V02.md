# M03-BATCH-003 — Master Remediation Codex Work Order V02

Milestone: **M03 — iOS Capture Foundation**
Purpose: **Third remediation pass after M03-BATCH-002 independent audit**
Tasks: **PL-0069, PL-0071 through PL-0093** (24 tasks)
Excluded accepted child: **PL-0070**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Canonical tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
Batch protocol: https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md
Previous remediation master audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_V01.md
This master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Master criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V02.md
Required master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_LOG_V02.md

## Authorization

Before material work, TASKS.md must show:
- Current Milestone: M03
- Current Task: M03-BATCH-003
- Current Task Status: READY
- Required Actor: CODEX
- PL-0070 already accepted
- PL-0068 still unchecked / OWNER_REQUIRED
- Next Task/Action pointing to this master prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Run:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Fast-forward only if safe. Never reset, rebase, force-push, destructively clean, or stash owner work.

Codex must never edit root TASKS.md or any ChatGPT audit artifact. Do not start M04. Do not fabricate PL-0068 physical evidence.

## Why a third remediation pass exists

The second remediation pass added substantial real framework, filesystem and UI code, but the independent audit found the remaining failures are concentrated at the last integration boundary:

- live runtime state versus disconnected helpers;
- selected-device/session ownership;
- wall-clock versus monotonic timestamp domains;
- source/record/state crash atomicity;
- authoritative schema/finalization/history coupling;
- destructive safety and failure-path evidence;
- tests that prove the real integrated seam rather than only nearby structs.

This batch must finish those boundaries. Do not solve findings by adding another unused model beside the production path.

## Ordered child execution

Execute exactly the 24 children below, in this order. PL-0070 is skipped because it is already independently accepted.

### 1. PL-0069 — Preview lifecycle/authorization

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CHATGPT_AUDIT_CRITERIA_V04.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_LOG_V04.md

Authorization must be resolved before lifecycle-start bookkeeping; denied→authorized return, start errors and repeated disappear/reappear must recover correctly with real bridge tests.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 2. PL-0071 — Selected-camera still capture

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CODEX_LOG_V03.md

Bind the real NextLevel photo adapter to the deterministic PL-0070 main-wide camera/session owner, clean pending delegates on stop/cancel and test the actual adapter seam.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 3. PL-0072 — Original image metadata

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CODEX_LOG_V03.md

Use ImageIO/CGImageSource to extract/preserve HEIF/JPEG metadata from immutable source bytes and prove derivative/dimension integrity boundaries.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 4. PL-0073 — Focus integration

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CODEX_LOG_V03.md

Require selected main-camera identity and shared configuration coordinator, observe real autofocus stabilization before lock, and drive visible live focus state.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 5. PL-0074 — Exposure integration

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CODEX_LOG_V03.md

Require selected-device/shared coordinator, persist actual exposure state into accepted-photo metadata, and expose real UI state with integrated tests.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 6. PL-0075 — White-balance integration

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CODEX_LOG_V03.md

Require selected-device/shared coordinator, observe real stabilization before lock, persist actual readings only, and expose live UI state.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 7. PL-0076 — Photo metadata schema validation

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_LOG_V03.md

Cross-validate encoded Swift wire JSON against the authoritative M02 schema and enforce all status/source/value/numeric invariants.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 8. PL-0077 — Camera recovery runtime

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CODEX_LOG_V03.md

Wire pending capture cancellation, permission signals, UI state and real bounded session restart into the recovery owner.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 9. PL-0078 — Live device health

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CODEX_LOG_V03.md

Run real monitor start/stop during active capture and make hard-stop actually block capture/session admission.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 10. PL-0079 — AR service lifecycle evidence

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CODEX_LOG_V03.md

Keep one SharedARSessionOwner and add behavior-bearing lifecycle/capability/duplicate-owner tests through ARTrackingService.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 11. PL-0080 — Pose timestamp-domain binding

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CODEX_LOG_V03.md

Bridge wall-clock capture time to ARKit monotonic time correctly and bind/persist pose alignment from the real accepted-still path.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 12. PL-0081 — Unified CoreMotion service

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_LOG_V03.md

Eliminate the parallel motion pipeline; MotionService must own attitude/quaternion + rotation rate and bind them to accepted captures.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 13. PL-0082 — Coordinate golden contract

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CODEX_LOG_V03.md

Add numeric X/Y/Z golden rotations and authoritative basis_conversion constant/schema checks while preserving fail-closed matrix math.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 14. PL-0083 — Live tracking recovery

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CODEX_LOG_V03.md

Use recovery hysteresis/warning models in the actual runtime with continuous tracking updates and retained diagnostics.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 15. PL-0084 — AR reset completion

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_LOG_V03.md

Drive real reset triggers through the one AR owner, complete epochs only after stable recovery and persist reset diagnostics.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 16. PL-0085 — Live pose overlay

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CODEX_LOG_V03.md

Continuously refresh tracking/pose/motion/epoch from real services with bounded lifecycle-aware updates.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 17. PL-0086 — Diagnostics units/privacy

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CODEX_LOG_V03.md

Add explicit units + basis_conversion and reuse the established diagnostics sanitizer/redaction boundary with golden tests.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 18. PL-0087 — New Scan callback workflow

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CODEX_LOG_V03.md

Make the wizard use the tested workflow seam, prove exact callback/no-callback behavior, and hand the resulting draft into real session creation.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 19. PL-0088 — Crash-atomic accepted-capture storage

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_LOG_V03.md

Unify the per-photo record contract and make source+record+state persistence recoverable after a crash at every transaction stage.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 20. PL-0089 — Gallery controls/state

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_LOG_V03.md

Use the canonical record format, add real delete/retake controls and atomically persist session state plus audit/file mutations.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 21. PL-0090 — Authoritative resume/discard

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CODEX_LOG_V03.md

Use the same reopen/recovery validator for launch discovery, install a real active session on Resume and execute safe discard.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 22. PL-0091 — Finalization success/failure

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CODEX_LOG_V03.md

Complete M02 preflight contract checks and add real successful atomic package plus no-partial failure/resumability tests.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 23. PL-0092 — Authoritative history state

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CODEX_LOG_V03.md

Connect real finalization output to history state and test finalized transitions plus corrupt/missing degraded cases.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 24. PL-0093 — Authoritative deletion

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CHATGPT_AUDIT_CRITERIA_V03.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CODEX_LOG_V03.md

Reject non-authoritative plans, wire history cleanup and detailed partial-failure reporting, and test symlink/partial/destructive boundaries.

Implement only this remediation scope, preserve prior passing behavior, run focused tests plus relevant regression, create a distinct implementation commit, then a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

## Integration gates

### Camera gate after PL-0078
Prove one coherent camera pipeline:
preview authorization/lifecycle → deterministic main-wide selection → real still capture → immutable source metadata → focus/exposure/WB → per-photo schema-valid metadata → recovery → live health admission.

No adapter may silently operate on an arbitrary camera or bypass the shared configuration/session owner.

### Tracking gate after PL-0086
Prove one coherent evidence pipeline:
single ARTrackingService owner + single MotionService → explicit timestamp-domain bridge → accepted-capture pose/motion binding → schema-aligned coordinates → recovery/reset epochs → live overlay → private-safe versioned diagnostics.

No duplicate sensor pipeline may remain active.

### Session gate after PL-0093
Prove one coherent persisted lifecycle:
New Scan → crash-atomic accepted-capture transaction → gallery mutations → launch resume/discard → atomic PackScan finalization → authoritative local history → authoritative safe deletion.

The same canonical per-photo/session record formats must be used by storage, gallery, resume, finalization, history and deletion.

## Per-child discipline

For each child:
1. read the latest child prompt, criteria and previous audit;
2. inspect final current main because earlier remediation children may provide shared fixes;
3. implement only the frozen child remediation;
4. add tests against the actual production seam;
5. run focused tests plus relevant regression;
6. verify `git diff --check`, `git diff -- TASKS.md`, protected audit files and privacy/signing scope;
7. create a distinct implementation commit;
8. publish the child log in a separate commit;
9. verify remote visibility;
10. continue only if the child is validation-green and no STOP condition exists.

## STOP conditions

Stop the entire batch for:
- authorization mismatch;
- unsafe repository state;
- a mandatory finding that requires M04 or a new ADR/owner decision;
- privacy/signing risk;
- need to edit TASKS.md;
- need to fabricate PL-0068 evidence;
- a mandatory regression that cannot be fixed inside the current child.

Publish truthful child/master evidence and end the master log `BATCH_STOPPED` if stopped.

## Final validation

After all 24 children:
- run the full repository-supported M03 regression;
- run project graph/static checks;
- verify PL-0070 remains unregressed;
- verify PL-0068 remains OWNER_REQUIRED;
- verify no M04 work;
- verify no TASKS/ChatGPT audit edits;
- verify each child has distinct implementation and log commits;
- inspect all changed files for secrets/signing/private assets/caches;
- run `git diff --check`.

Create:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_LOG_V02.md

Index all 24 children with prompt/criteria/audit URLs, start commit, implementation commit, log commit, validation and runtime limitations.

End exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not self-audit.
