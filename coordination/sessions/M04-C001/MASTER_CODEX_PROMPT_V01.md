# M04-BATCH-001 — Master Codex Work Order V01

Milestone: **M04 — Guided Capture & Quality Intelligence**
Tasks: **PL-0094 through PL-0118** (25 tasks)
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Canonical tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
This master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_PROMPT_V01.md
Master audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md
Required master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_LOG_V01.md

## Authorization gate

Before material work, TASKS.md must show:
- Current Milestone: M04
- Current Task: M04-BATCH-001
- Current Task Status: READY
- Required Actor: CODEX
- M03 marked complete
- PL-0068 still unchecked / OWNER_REQUIRED
- Next Task/Action pointing to this master prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Before work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Fast-forward only if safe. Never reset, rebase, force-push, destructively clean or stash owner work.

Codex must never edit:
- root `TASKS.md`;
- any `*_CHATGPT_AUDIT_*.md`;
- accepted M03 behavior merely for convenience.

Do not start M05.

## Existing architecture that M04 must extend

M03 is independently accepted. Reuse its production architecture:

- one deterministic iPhone rear main-wide camera selection;
- one NextLevel preview/still-capture path;
- one CameraRecoveryOwner;
- one health-gated still-capture admission path;
- one CameraDeviceControlDriver/configuration path for focus/exposure/WB;
- one ARTrackingService/SharedARSessionOwner;
- one MotionService/CoreMotion owner;
- monotonic pose/motion alignment;
- immutable accepted source persistence;
- canonical accepted-capture/session transaction records;
- crash-safe resume/finalization/history/deletion;
- PackScan coordinate and metadata contracts.

M04 must **extend** these seams. It must not introduce parallel camera, AR, motion, capture, session or quality ownership.

## Physical-evidence rule

PL-0068 remains OWNER_REQUIRED because the owner currently lacks a printer. M04 may continue under the existing owner-authorized exception, but:

- never mark PL-0068 complete;
- never fabricate owner calibration or iPhone physical evidence;
- thresholds tuned only from deterministic fixtures/synthetic data must be labeled provisional/test-calibrated;
- code must make later owner/device calibration possible without replacing the algorithm contract.

## Ordered children

Execute exactly these 25 tasks in order:

### 1. PL-0094 — Sharpness metric

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0094_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0094_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0094_CODEX_LOG_V01.md

Implement deterministic sharpness analysis, configurable thresholds and truthful provisional calibration harness.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 2. PL-0095 — Motion-blur warning

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0095_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0095_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0095_CODEX_LOG_V01.md

Combine image blur with timestamp-aligned CoreMotion evidence and explainable warning reasons.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 3. PL-0096 — Highlight clipping

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0096_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0096_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0096_CODEX_LOG_V01.md

Measure highlight clipping for glossy packaging with configurable tolerated/broad-clipping thresholds.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 4. PL-0097 — Shadow clipping

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0097_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0097_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0097_CODEX_LOG_V01.md

Measure underexposure/shadow clipping with explainable metrics and configurable thresholds.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 5. PL-0098 — Object framing

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0098_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0098_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0098_CODEX_LOG_V01.md

Score package size/framing and distinguish too-small, acceptable and cropped/too-large states.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 6. PL-0099 — Background complexity

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0099_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0099_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0099_CODEX_LOG_V01.md

Warn on cluttered photogrammetry backgrounds using bounded live analysis.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 7. PL-0100 — Frame quality decision

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0100_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0100_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0100_CODEX_LOG_V01.md

Combine all quality metrics into deterministic ACCEPT/REJECT with stable reason codes.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 8. PL-0101 — Quality logging

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CODEX_LOG_V01.md

Persist metrics/decisions for every candidate and accepted/rejected frame.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 9. PL-0102 — Orbit coverage model

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0102_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0102_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0102_CODEX_LOG_V01.md

Track azimuth/elevation coverage bins from accepted PackScan pose evidence.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 10. PL-0103 — Coverage visualization

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0103_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0103_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0103_CODEX_LOG_V01.md

Show authoritative captured/missing sectors in SwiftUI without new tracking ownership.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 11. PL-0104 — Auto capture

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CODEX_LOG_V01.md

Capture automatically only when pose, coverage, overlap and quality gates all pass.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 12. PL-0105 — Duplicate prevention

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0105_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0105_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0105_CODEX_LOG_V01.md

Reject near-duplicate candidates while preserving prior immutable accepted sources.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 13. PL-0106 — Bottle capture rings

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CODEX_LOG_V01.md

Require lower/middle/upper ring coverage for standard bottle mode.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 14. PL-0107 — Top/neck detail pass

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CODEX_LOG_V01.md

Add closure/neck/shoulder detail coverage with explicit pass metadata.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 15. PL-0108 — Bottom/base detail pass

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0108_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0108_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0108_CODEX_LOG_V01.md

Add physically feasible optional base coverage with explicit unavailable/skip state.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 16. PL-0109 — Completion guidance

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CODEX_LOG_V01.md

Compute deterministic completion score plus explicit missing-area guidance.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 17. PL-0110 — Manual override

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0110_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0110_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0110_CODEX_LOG_V01.md

Allow manual capture with warnings while preserving non-overridable safety gates.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 18. PL-0111 — Matte/HDPE preset

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0111_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0111_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0111_CODEX_LOG_V01.md

Configure shared quality/coverage policies for matte/HDPE packaging.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 19. PL-0112 — Glossy/PET preset

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0112_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0112_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0112_CODEX_LOG_V01.md

Configure highlight control and denser coverage for glossy/PET packaging.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 20. PL-0113 — Transparent warning mode

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0113_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0113_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0113_CODEX_LOG_V01.md

Provide truthful preparation/treatment warnings without claiming unsupported reliability.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 21. PL-0114 — Asymmetric/Jerrycan mode

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0114_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0114_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0114_CODEX_LOG_V01.md

Require stronger front/back/side/handle-region coverage.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 22. PL-0115 — Closure/Cap detail mode

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0115_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0115_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0115_CODEX_LOG_V01.md

Provide tighter detail capture while preserving supported main-camera lens policy.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 23. PL-0116 — Turntable mode

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0116_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0116_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0116_CODEX_LOG_V01.md

Track angle-indexed coverage with truthful evidence-source labeling.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 24. PL-0117 — Capture protocol screen

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0117_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0117_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0117_CODEX_LOG_V01.md

Show preset-driven preparation, lighting and background guidance.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 25. PL-0118 — Scan-suitability preflight

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0118_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0118_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0118_CODEX_LOG_V01.md

Gate scan start with deterministic blockers/warnings across preset, device, health and calibration state.

Read the frozen child prompt/criteria, preserve the accepted M03 architecture, implement only this task, add behavior-bearing tests, create a distinct implementation commit, then publish the child log in a separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

## Integration gate after PL-0101 — Live quality engine

Verify one coherent candidate-frame quality pipeline:

candidate frame → sharpness → motion blur → highlight clipping → shadow clipping → framing → background complexity → deterministic decision → structured metrics log.

Requirements:
- stable reason codes;
- raw metrics retained;
- unavailable optional data represented truthfully;
- hard reject precedence deterministic;
- candidate/rejected logging does not corrupt accepted-session state;
- no black-box quality score.

## Integration gate after PL-0110 — Guided orbit capture

Verify one coherent guidance/capture pipeline:

accepted pose → orbit coverage → live coverage UI → quality-qualified target sector → duplicate/overlap policy → automatic capture → accepted session transaction → completion/missing-area guidance.

Requirements:
- no synthetic/stale pose becomes coverage;
- auto-capture uses the existing health-gated still-capture path;
- no duplicate camera/AR owner;
- lower/middle/upper plus detail passes remain explicit;
- manual override retains warnings and cannot bypass hard safety/capture failures.

## Integration gate after PL-0118 — Packaging presets and preflight

Verify presets/modes configure the shared quality/coverage engine rather than fork it.

Required end-to-end state:

New Scan preset/mode → capture protocol/preparation guidance → scan-suitability preflight → quality policy → coverage policy → capture/override → session persistence.

Requirements:
- Matte/HDPE, Glossy/PET, Transparent, Asymmetric/Jerrycan, Closure/Cap and Turntable behavior is explicit/versioned;
- preset/effective policy is persisted;
- transparent treatment remains guidance/acknowledgement, not a false guarantee;
- turntable evidence source is distinguishable from AR freehand pose;
- PL-0068 unavailable owner calibration is represented truthfully.

## Per-child execution discipline

For every child:
1. read TASKS.md, this master prompt, child prompt and child criteria;
2. verify authorization remains valid;
3. inspect current `main`, including prior M04 child changes;
4. implement only the frozen child scope;
5. add behavior-bearing positive, negative, unavailable-data and exact-boundary tests;
6. run focused + relevant regression/project/static checks;
7. run `git diff --check`;
8. verify `git diff -- TASKS.md` is empty and ChatGPT audit artifacts are untouched;
9. review privacy/signing/secrets/caches;
10. create a distinct implementation/evidence commit;
11. publish the child log in a separate log-only commit;
12. verify remote visibility before continuing.

## STOP conditions

Stop the full batch if:
- authorization/repository safety fails;
- a task requires M05 or later-milestone implementation;
- a genuine owner/ADR decision is required;
- a required physical claim cannot be made truthfully;
- protected files would need Codex edits;
- privacy/signing risk appears;
- a mandatory regression cannot be repaired inside the current child.

Publish truthful evidence and end the master log `BATCH_STOPPED` if stopped.

## Validation requirements

After all 25:
- run all repository-supported deterministic M04/M03 regression;
- run project/static graph checks;
- verify M03 accepted behavior remains unregressed;
- verify PL-0068 remains OWNER_REQUIRED;
- verify no M05 work;
- run `git diff --check`;
- prove TASKS.md/ChatGPT audits untouched;
- inspect privacy/signing/cache scope;
- verify every child has a distinct implementation commit and log-only commit.

Native Swift/Xcode/simulator/physical-iPhone results may be claimed only if actually executed. Windows-side builder evidence is not physical validation.

## User-facing link policy

Local paths are allowed internally only.

Every user-facing repository reference in progress/handoff messages must be a full GitHub URL. Never show `C:\Users\...`, `C:/Users/...`, `file://` URLs or local-path Markdown links.

## Final handoff

Publish:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_LOG_V01.md

The master log must index all 25 children with:
- full GitHub prompt/criteria/log links;
- start commit;
- implementation commit;
- child-log commit;
- validation results;
- limitations/physical-evidence status.

End exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not self-audit.
