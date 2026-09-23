# PL-0089 — Codex Work Order V01

Task: **PL-0089 — Add photo gallery for accepted frames with delete/retake controls.**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_PROMPT_V01.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_LOG_V01.md

## Batch authorization gate

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the M03 master prompt/criteria, this child prompt/criteria, and relevant accepted M01/M02 contracts. TASKS.md must authorize `M03-BATCH-001` / `READY` / `CODEX` and point to the M03 master prompt. PL-0068 must remain unchecked / OWNER_REQUIRED. Otherwise stop `TASK_STATE_MISMATCH`.

Never edit TASKS.md or ChatGPT audit artifacts. Never fabricate physical-device results. Do not start M04.

## Scope

Accepted-frame gallery UI/view model, session-storage mutation rules and tests.

## Mandatory requirements

1. Show accepted frames from the session store using derived thumbnails/previews without modifying immutable source image bytes.
2. Provide explicit delete and retake controls with confirmation/clear semantics and stable capture identities.
3. When an accepted frame is removed, update session indexes/metadata safely while retaining an audit/replacement trace where the storage contract requires it.
4. Retake creates a new capture identity; it must not silently overwrite the previous immutable source file.
5. Add model/view-model tests for gallery ordering, delete, retake and missing-thumbnail/source error states.

## Engineering constraints

- Reuse the existing SwiftUI app, Swift 6 strict-concurrency configuration, iOS 17 baseline, NextLevel 0.19.1 pin, service seams, diagnostics/privacy rules and PackScan contracts.
- Keep source-of-truth ownership explicit. Prefer small testable models/adapters over framework calls scattered across views.
- Preserve simulator-safe behavior. Simulator/public synthetic evidence must never be described as physical iPhone evidence.
- If a technically necessary adjacent change is required, keep it minimal and justify it in the child log.
- Do not implement later child features merely for convenience unless the dependency is a tiny non-user-visible seam explicitly documented in the log.

## Validation and handoff

Run all relevant validation available in the builder environment: focused deterministic tests, project/source membership checks, any supported Swift/static checks, xcodebuild only when Xcode/macOS is genuinely available, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review, and privacy/secrets/signing review.

If xcodebuild or native iPhone execution is unavailable, report that truthfully; that limitation alone does not authorize fabricated evidence.

Commit the child implementation/evidence separately, publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_LOG_V01.md, verify remote visibility, and end the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Then continue to the next master-ordered child only if validations are green and no batch STOP condition exists.
