# M03-BATCH-002 — Master Remediation Codex Work Order V01

Milestone: **M03 — iOS Capture Foundation**
Purpose: **Remediate the 24 failed children from M03-BATCH-001**
Tasks: **PL-0069, PL-0071 through PL-0093; PL-0070 is excluded because it is already AUDITED_PASS**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Canonical tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
Batch protocol: https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md
Previous milestone audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_CHATGPT_AUDIT_V01.md
This master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Master remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V01.md
Required master remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_LOG_V01.md

## Authorization state

This batch exists because M03-BATCH-001 independently audited as:
- PL-0070: **AUDITED_PASS**
- the other 24 M03 children: **CHANGES_REQUIRED**

PL-0068 remains separately unchecked / OWNER_REQUIRED because the owner currently lacks printer access for the physical benchmark. This remediation batch must not alter or fabricate PL-0068.

Before material work, TASKS.md must show:
- Current Milestone: M03
- Current Task: M03-BATCH-002
- Current Task Status: READY
- Required Actor: CODEX
- PL-0070 checked/accepted
- PL-0068 still unchecked / OWNER_REQUIRED
- Next Task/Action pointing to this master remediation prompt

Otherwise stop `TASK_STATE_MISMATCH`.

## Synchronization and protected files

Before material work run:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Fast-forward only when safe. Never reset, rebase, force-push, destructively clean or stash owner work.

Codex must never edit:
- root `TASKS.md`;
- any `*_CHATGPT_AUDIT_*.md`;
- the accepted PL-0070 implementation merely to make unrelated remediation convenient unless a direct compatibility defect is proven and the batch stops for audit.

Do not start M04.

## Remediation strategy

The first batch produced many valid policies/data models but repeatedly stopped at the seam between those models and the real product flow. This remediation must therefore prioritize **integration, ownership, persistence and behavior**, not add more disconnected structs.

Key architectural goals across the remediation:
1. exactly one coherent camera/session ownership path for NextLevel + selected AVFoundation device;
2. existing M01 service seams remain the real app boundaries rather than parallel controllers;
3. framework events feed deterministic state machines and those states feed real SwiftUI UI;
4. accepted captures bind immutable source bytes, PackScan-compatible metadata, pose/motion evidence and session persistence coherently;
5. filesystem lifecycle is authoritative and crash-safe from New Scan through resume/finalize/history/delete;
6. simulator/synthetic evidence remains explicitly non-physical;
7. no native Xcode/iPhone success is claimed unless actually executed.

## Ordered remediation children

Execute exactly this order, skipping the already accepted PL-0070:

### 1. PL-0069 — NextLevel preview / SwiftUI bridge

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_PROMPT_V03.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CHATGPT_AUDIT_CRITERIA_V03.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_LOG_V03.md

Wire real authorization/start error states and fix symmetric preview attach/detach across repeated lifecycle transitions.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 2. PL-0071 — High-resolution still capture

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CODEX_LOG_V02.md

Implement the real NextLevel photo request/delegate path, selected-main-camera binding, exact-once completion and original bytes/dimensions.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 3. PL-0072 — Original source + metadata preservation

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CODEX_LOG_V02.md

Persist immutable original bytes, extract/preserve ImageIO metadata, separate derivatives and verify integrity.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 4. PL-0073 — Focus control

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CODEX_LOG_V02.md

Integrate selected-camera guided autofocus/stabilization then optional lock, shared serialization and visible focus state.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 5. PL-0074 — Exposure control

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CODEX_LOG_V02.md

Use shared camera configuration serialization, integrate metering/lock state, persist exposure metadata and expose UI state.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 6. PL-0075 — White balance

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CODEX_LOG_V02.md

Use real stabilization before lock, capture actual readings, serialize configuration and expose UI state.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 7. PL-0076 — Per-photo metadata

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_LOG_V02.md

Match M02 photo-metadata JSON schema exactly and persist source+metadata atomically with cross-contract tests.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 8. PL-0077 — Camera recovery

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CODEX_LOG_V02.md

Wire real permission/interruption/runtime-error events, idempotent observers, in-flight capture safety and user-visible recovery.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 9. PL-0078 — Device health

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CODEX_LOG_V02.md

Read real thermal/storage/battery state, run preflight/live monitoring and bind hard-stop/warnings to capture flow.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 10. PL-0079 — AR tracking service

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CODEX_LOG_V02.md

Put physical ARKit behind existing ARTrackingService and establish one ARSession owner with simulator parity.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 11. PL-0080 — AR pose sampling

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CODEX_LOG_V02.md

Sample real ARFrame transforms/timestamps, validate/buffer them and bind eligible pose to accepted captures.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 12. PL-0081 — CoreMotion alignment

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_LOG_V02.md

Put CoreMotion behind MotionService, expose failures and bind bounded motion samples to accepted captures.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 13. PL-0082 — Coordinate math

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CODEX_LOG_V02.md

Fail closed on invalid matrices and add translation/axis-rotation/composition/inverse/round-trip golden tests.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 14. PL-0083 — Tracking degradation warnings

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CODEX_LOG_V02.md

Add visible warning state, recovery hysteresis/stability and retained degradation diagnostics.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 15. PL-0084 — AR reset/relocalization

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_LOG_V02.md

Execute reset through one ARSession owner with run options, epoch diagnostics and integrated reset triggers.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 16. PL-0085 — Pose debug overlay

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CODEX_LOG_V02.md

Drive overlay from real AR/pose/motion/epoch state and show truthful live pose/orientation or unavailable state.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 17. PL-0086 — Pose diagnostics

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CODEX_LOG_V02.md

Freeze units/timebase/frame semantics, validate malformed pose/motion, apply privacy redaction and test boundaries.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 18. PL-0087 — New Scan workflow

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CODEX_LOG_V02.md

Make wizard reachable, show validation state and test cancel/start/invalid/mode mappings.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 19. PL-0088 — Crash-safe storage

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_LOG_V02.md

Add per-photo records, accepted-capture transaction, reopen/stale-temp recovery and filesystem failure tests.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 20. PL-0089 — Photo gallery

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_LOG_V02.md

Add real store-backed gallery UI and persist delete/retake/replacement semantics with missing-file handling.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 21. PL-0090 — Session resume

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CODEX_LOG_V02.md

Discover/reopen incomplete sessions on launch, reconstruct full state and provide Resume/Discard/blocked-corrupt flow.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 22. PL-0091 — PackScan finalization

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CODEX_LOG_V02.md

Validate M02 manifest/photo/source/checksum relationships, actionable errors and full atomic success/failure tests.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 23. PL-0092 — Local scan history

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CODEX_LOG_V02.md

Derive authoritative history from disk, add UI, degraded entries and state-transition tests.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

### 24. PL-0093 — Safe deletion

Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CODEX_PROMPT_V02.md  
Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CHATGPT_AUDIT_CRITERIA_V02.md  
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CODEX_LOG_V02.md

Bind deletion to validated session identity, add confirmation UI, coordinated cleanup and destructive-boundary filesystem tests.

Read the previous independent audit referenced by the child prompt. Preserve every previously passing behavior, close every audit finding, produce behavior-bearing tests, create a distinct remediation implementation/evidence commit, then publish the child remediation log in a separate log-only commit before continuing.

## Integration checkpoints

### After PL-0078
Verify camera control works as one architecture:
- preview lifecycle and permission states;
- deterministic selected main lens;
- real still capture;
- immutable original source/metadata;
- focus/exposure/WB through one serialized camera owner;
- recovery event wiring;
- real health monitoring;
- capture UI reflects truthful states.

### After PL-0086
Verify tracking/motion works as one architecture:
- ARKit behind ARTrackingService;
- CoreMotion behind MotionService;
- one ARSession;
- bounded timestamped pose/motion buffers;
- accepted-capture alignment;
- validated coordinate conversion;
- degradation hysteresis;
- reset epochs;
- live debug overlay;
- deterministic private-safe diagnostics.

### After PL-0093
Verify session lifecycle works end-to-end:
New Scan → validated session creation → accepted capture transaction → gallery/delete/retake → app termination/resume → atomic .packscan finalization → local history → confirmed bounded deletion.

## Per-child execution discipline

For each child:
1. read the remediation prompt, remediation criteria and previous independent audit;
2. verify master authorization remains valid;
3. inspect current main because earlier remediation children may legitimately provide shared foundations;
4. implement only the child remediation scope while preserving already-passing behavior;
5. run focused + relevant regression validation;
6. verify `git diff --check` and protected TASKS/audit files;
7. commit remediation implementation/evidence;
8. publish the matching remediation child log in a separate log-only commit;
9. verify remote visibility;
10. continue only when the child is validation-green and no STOP condition exists.

## STOP conditions

Stop the entire remediation batch if:
- authorization or repository safety fails;
- a mandatory finding cannot be fixed inside M03;
- an ADR/owner decision is genuinely required;
- a privacy/security/signing risk appears;
- root TASKS.md would need a Codex edit;
- PL-0068 physical evidence would need to be fabricated;
- M04 work would be required.

When stopped, publish the current child log and master remediation log with `BATCH_STOPPED`.

## Final batch validation

After all 24 remediation children:
- verify PL-0070 remains unregressed;
- run repository-supported deterministic M03 regression;
- run project graph/static validation;
- run `git diff --check`;
- prove Codex never modified TASKS.md or ChatGPT audits;
- inspect exact changed files and privacy/signing boundaries;
- confirm no M04 work;
- confirm PL-0068 remains OWNER_REQUIRED;
- confirm every remediation child has distinct implementation and log commits.

Create:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_LOG_V01.md

Index every remediation child with prompt/criteria/audit URL, start commit, remediation implementation commit, child-log commit, validation results and limitations.

End exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not self-audit.
