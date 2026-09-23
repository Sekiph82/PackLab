# M03-BATCH-001 — Master Codex Work Order V01

Milestone: **M03 — iOS Capture Foundation**
Tasks: **PL-0069 through PL-0093 inclusive (25 tasks)**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Canonical tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
Batch protocol: https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md
This master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_CODEX_PROMPT_V01.md
Master audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md
Required master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_CODEX_LOG_V01.md

## Owner authorization and open M02 gate

The owner explicitly authorized continuing into M03 while **PL-0068 remains open / OWNER_REQUIRED** because physical printed-mat verification cannot currently be completed without printer access.

This authorization is an execution-order exception only. It does **not**:
- mark PL-0068 complete;
- permit fabricated physical benchmark evidence;
- permit Codex to edit TASKS.md;
- permit M04 work;
- waive any M03 child audit.

PL-0068 must remain unchecked and OWNER_REQUIRED throughout this batch.

## Master authorization gate

Before any material work:

1. Read `TASKS.md`, `AGENTS.md`, `coordination/MILESTONE_BATCH_PROTOCOL.md`, this master prompt, its master criteria, and all 25 child prompts/criteria listed below.
2. `TASKS.md` must explicitly show:
   - Current Milestone: M03
   - Current Task: M03-BATCH-001
   - Current Task Status: READY
   - Required Actor: CODEX
   - Next Task/Action pointing to this master prompt
   - Open Owner Gate recording PL-0068 unchecked / OWNER_REQUIRED
3. Run:
   - `git fetch origin main --prune`
   - `git rev-list --left-right --count HEAD...origin/main`
   - `git status --porcelain`
4. Require a safe synchronized state. Fast-forward is allowed. Never reset, rebase, force-push, destructively clean, or stash owner work.

If authorization or safe synchronization fails, stop `TASK_STATE_MISMATCH` or `REPOSITORY_STATE_UNSAFE`.

## Batch execution contract

Execute **exactly these 25 children, in order: PL-0069 → PL-0093**.

For each child:
1. read the frozen child prompt and criteria;
2. verify the master authorization still exists;
3. implement only that child scope;
4. run its focused tests/static/project checks and required Git/privacy checks;
5. create a distinct implementation/evidence commit;
6. publish the matching child Codex log in a separate log-only commit;
7. verify remote visibility of implementation and log;
8. continue to the next child only when validations are green and no STOP condition exists.

Codex must not:
- edit `TASKS.md`;
- create or edit ChatGPT audit artifacts;
- self-mark any PL task complete;
- start M04;
- close/fabricate PL-0068;
- fold multiple child implementations into one indistinguishable commit;
- claim Xcode/native-device execution that did not actually occur.

The lack of physical iPhone execution in the builder environment is not, by itself, permission to fabricate evidence. Where hardware/Xcode is unavailable, maximize deterministic testability through injected descriptors/state/timestamps/filesystem fixtures and report the runtime limitation truthfully.

## Architecture that must remain coherent

M03 builds on accepted M01/M02 foundations:
- iOS 17 baseline;
- Swift 6 strict concurrency and warnings-as-errors;
- NextLevel pinned exactly to 0.19.1 unless a child proves a blocking incompatibility and stops for an architecture decision;
- existing `CameraService`, `ARTrackingService`, `MotionService`, storage/transfer and simulator fallback seams;
- PackScan schemas/contracts and Swift writer from M02;
- diagnostics redaction/privacy behavior;
- no LiDAR assumption for iPhone 16 Standard;
- immutable source evidence and explicit unavailable states instead of invented sensor/camera data.

Keep framework ownership narrow, state machines explicit, and pure policy/math/serialization logic independently testable.

## Detailed ordered child plan

### 1. PL-0069 — NextLevel preview / SwiftUI UIKit bridge

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_PROMPT_V02.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CHATGPT_AUDIT_CRITERIA_V02.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_LOG_V02.md

Create a real NextLevel-backed preview surface behind a narrow UIKit bridge, present truthful running/denied/simulator/error states, make lifecycle idempotent, preserve NextLevel 0.19.1 and do not leak session ownership into ordinary SwiftUI views.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 2. PL-0070 — Deterministic iPhone 16 rear main-camera selection

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0070_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0070_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0070_CODEX_LOG_V01.md

Enumerate rear AVCaptureDevice candidates by device type/position, select builtInWideAngleCamera deterministically, expose stable lens identity, reject ambiguous/unsupported candidates and keep the policy independently testable.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 3. PL-0071 — High-resolution still capture

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CODEX_LOG_V01.md

Implement reconstruction-source still capture through the selected camera, preserve original source bytes/dimensions, make completion single-shot and failure-safe, and avoid social-media-style processing.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 4. PL-0072 — Original metadata/source preservation

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CODEX_LOG_V01.md

Persist immutable original still bytes with dimensions/orientation/available metadata intact, separate previews/thumbnails from source evidence, and fail on destructive or mismatched transformations.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 5. PL-0073 — Guided autofocus + optional focus lock

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CODEX_LOG_V01.md

Implement supported autofocus guidance and optional lock with truthful capability/state reporting, serialized device configuration and deterministic policy/state tests.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 6. PL-0074 — Exposure metering + optional exposure lock

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CODEX_LOG_V01.md

Implement supported exposure metering/lock, validate device bounds/capabilities, record actual exposure state and recover safely from configuration errors.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 7. PL-0075 — White-balance stabilization/lock

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CODEX_LOG_V01.md

Implement supported continuous white balance stabilization and optional lock, preserve actual device readings/modes only, avoid fabricated temperature/tint, and test capability/state behavior.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 8. PL-0076 — Per-photo camera metadata persistence

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_LOG_V01.md

Persist PackScan-compatible per-photo metadata for every accepted still, atomically bind metadata to immutable source images, explicitly represent unavailable hardware fields and add contract tests.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 9. PL-0077 — Camera interruption/error recovery

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CODEX_LOG_V01.md

Add explicit recovery state machine for permission denial, runtime errors, interruptions and restart, prevent duplicate sessions/listeners, preserve accepted captures and provide actionable UI messages.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 10. PL-0078 — Thermal/storage/battery warnings

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CODEX_LOG_V01.md

Monitor device thermal state, storage and battery using injectable health snapshots, define deterministic warning/hard-stop policy, evaluate before/during capture and keep simulator behavior truthful.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 11. PL-0079 — Non-LiDAR ARKit world tracking

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CODEX_LOG_V01.md

Implement ARWorldTrackingConfiguration for the iPhone 16 Standard baseline without LiDAR-only features, expose it through ARTrackingService and preserve simulator unavailable behavior.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 12. PL-0080 — Timestamp-aligned AR camera transforms

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CODEX_LOG_V01.md

Sample ARFrame transforms/tracking state on a documented timebase, align poses to accepted capture timestamps with explicit tolerances, preserve stale/missing evidence as unavailable and test alignment edge cases.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 13. PL-0081 — Timestamp-aligned CoreMotion data

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_LOG_V01.md

Record attitude/rotation-rate samples with bounded buffering and monotonic timestamps, align to capture timestamps using explicit age limits, preserve simulator no-evidence behavior and test stale/missing cases.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 14. PL-0082 — App-local to PackScan coordinate conversion

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CODEX_LOG_V01.md

Freeze handedness/axes/units/matrix/origin conventions, implement explicit transform conversion matching M02 PackScan pose contracts and add mathematical golden/round-trip tests.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 15. PL-0083 — AR tracking degradation warnings

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CODEX_LOG_V01.md

Map AR tracking states into stable PackLab quality states, surface limited/unavailable/recovering warnings, gate pose evidence appropriately and test flapping/recovery transitions.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 16. PL-0084 — Session reset/relocalization

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_LOG_V01.md

Implement explicit AR/capture reset behavior with localization epochs, prevent pose mixing across resets, preserve accepted photos/diagnostics and test repeated/reset-during-active scenarios.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 17. PL-0085 — Pose visualizer/debug overlay

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0085_CODEX_LOG_V01.md

Add a toggleable development overlay driven by the existing real AR/motion state, visibly distinguish unavailable/simulator states and avoid a second sensor pipeline or per-frame heavy work.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 18. PL-0086 — Pose diagnostics export

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CODEX_LOG_V01.md

Export deterministic versioned pose/motion alignment diagnostics with units/timebases/frame version, privacy redaction and malformed/non-finite data rejection; do not implement Windows ingest.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 19. PL-0087 — New Scan wizard

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CODEX_LOG_V01.md

Create a SwiftUI wizard for package name/type, capture mode and optional notes, use stable M02 capture-mode IDs, validate fields and produce a deterministic session draft.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 20. PL-0088 — Crash-safe incremental session storage

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_LOG_V01.md

Define local session layout, use atomic incremental writes, keep accepted raw photos immutable, isolate temp files and add interruption/stale-temp/duplicate-ID/reopen tests.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 21. PL-0089 — Accepted-frame gallery with delete/retake

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_LOG_V01.md

Render derived previews from session storage, provide explicit delete/retake semantics, preserve immutable source identity/history and test gallery mutation/error cases.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 22. PL-0090 — Resume after app termination

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CODEX_LOG_V01.md

Discover incomplete sessions, reconstruct state from persisted records, preserve sequence/history/epochs, block corrupt sessions safely and test clean/crash/missing/version-mismatch resumes.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 23. PL-0091 — Validated .packscan finalization

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CODEX_LOG_V01.md

Define M03 minimum finalization gate, validate manifest/photo/source/checksum relationships, create .packscan atomically through the existing writer, keep failed sessions resumable and test positive/negative cases.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 24. PL-0092 — Local scan history

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CODEX_LOG_V01.md

Show preview/date/package/export state from authoritative session/finalization records, handle degraded entries explicitly, define deterministic sorting and avoid full-resolution loading for history UI.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

### 25. PL-0093 — Safe confirmed deletion

Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CODEX_PROMPT_V01.md  
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CODEX_LOG_V01.md

Require confirmation, restrict deletion to validated PackLab-owned canonical paths, prevent traversal/symlink escape, clean associated data consistently, expose partial failure and test destructive-boundary attacks.

Execution boundary: implement only this child's frozen scope, run its own validations, create a distinct implementation/evidence commit and a distinct child-log commit, verify both remotely, then continue only if the child is validation-green and no master STOP condition exists.

## Cross-child integration gates

After PL-0078, verify the camera-control layer is internally coherent: one camera/session ownership model, deterministic main-lens identity, original high-resolution still preservation, focus/exposure/WB controls, per-photo metadata, recovery and device-health warnings.

After PL-0086, verify AR/motion integration is coherent: one AR session, one motion service, explicit timebases, pose/motion alignment, frozen coordinate conversion, tracking degradation/reset epochs, truthful debug overlay and deterministic diagnostics export.

After PL-0093, verify capture-project lifecycle is coherent: New Scan → crash-safe session storage → accepted-frame gallery → termination/resume → validated atomic .packscan finalization → local history → safe deletion.

Do not substitute future M04 guided-capture/quality features to fill gaps. M03 must end as a solid capture foundation, not a partially started M04.

## Master validation

After the last child implementation/log:

1. Inspect the final diff/history from the authorized batch start.
2. Verify exactly PL-0069..PL-0093 were executed and no M04 task was started.
3. Verify PL-0068 remains unchanged/unclosed except its already-existing owner-required tracker note.
4. Verify every child has:
   - frozen prompt and criteria;
   - distinct implementation/evidence commit;
   - child log commit;
   - remote GitHub visibility;
   - `READY_FOR_INDEPENDENT_AUDIT` handoff.
5. Run every repository-supported relevant deterministic test/static validation available on the builder host.
6. Run `git diff --check`.
7. Verify builder never changed `TASKS.md`.
8. Review all batch changes for credentials, Apple signing material, provisioning private data, private scans, confidential supplier/Kenya material, user-private paths and generated caches.
9. Record Xcode/macOS/iPhone limitations exactly. Do not turn static/simulator validation into a device claim.

## Master STOP conditions

Stop the whole batch immediately if any child encounters:
- task/master authorization mismatch;
- unsafe repository divergence;
- a frozen mandatory validation failure that cannot be corrected within that child;
- an architecture contradiction requiring an ADR outside M03;
- a privacy/security/signing risk;
- an owner decision genuinely required to proceed;
- any need for Codex to edit TASKS.md;
- any need to start M04.

On STOP:
- finish/push only authorized evidence for the current child;
- publish its child log truthfully;
- publish the master log with `BATCH_STOPPED`;
- do not continue later children.

## Master log

After all 25 children complete, create:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_CODEX_LOG_V01.md

The master log must index, for every child:
- task ID;
- child prompt URL;
- criteria URL;
- synchronized child start commit;
- implementation/evidence commit;
- child-log commit;
- child-log URL;
- validation summary;
- known runtime/device limitation.

It must also include batch-start commit, final commit, exact child order, full-scope/privacy review, confirmation that PL-0068 remained OWNER_REQUIRED, and confirmation that M04 did not start.

End the master log exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not self-audit.
