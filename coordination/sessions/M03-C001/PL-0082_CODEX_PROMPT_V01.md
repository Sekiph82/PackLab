# PL-0082 — Codex Work Order V01

Task: **PL-0082 — Define app-local coordinate frame and conversion into PackScan coordinates.**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CODEX_PROMPT_V01.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CODEX_LOG_V01.md

## Batch authorization gate

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the M03 master prompt/criteria, this child prompt/criteria, and relevant accepted M01/M02 contracts. TASKS.md must authorize `M03-BATCH-001` / `READY` / `CODEX` and point to the M03 master prompt. PL-0068 must remain unchecked / OWNER_REQUIRED. Otherwise stop `TASK_STATE_MISMATCH`.

Never edit TASKS.md or ChatGPT audit artifacts. Never fabricate physical-device results. Do not start M04.

## Scope

Coordinate-system contract/documentation, transform utilities and mathematical tests.

## Mandatory requirements

1. Define handedness, axis directions, units, matrix storage/order and origin semantics for the app-local AR/camera frame and canonical PackScan frame.
2. Implement explicit conversion functions for transforms/poses without hidden transpose, sign-flip or unit assumptions.
3. Document the conversion contract close to code and ensure it matches the accepted M02 PackScan AR pose schema.
4. Add golden mathematical tests for identity, translation, axis rotations, composition and invertibility/round-trip within tolerance.
5. Do not mix screen/image-pixel coordinates with world-coordinate transforms.

## Engineering constraints

- Reuse the existing SwiftUI app, Swift 6 strict-concurrency configuration, iOS 17 baseline, NextLevel 0.19.1 pin, service seams, diagnostics/privacy rules and PackScan contracts.
- Keep source-of-truth ownership explicit. Prefer small testable models/adapters over framework calls scattered across views.
- Preserve simulator-safe behavior. Simulator/public synthetic evidence must never be described as physical iPhone evidence.
- If a technically necessary adjacent change is required, keep it minimal and justify it in the child log.
- Do not implement later child features merely for convenience unless the dependency is a tiny non-user-visible seam explicitly documented in the log.

## Validation and handoff

Run all relevant validation available in the builder environment: focused deterministic tests, project/source membership checks, any supported Swift/static checks, xcodebuild only when Xcode/macOS is genuinely available, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review, and privacy/secrets/signing review.

If xcodebuild or native iPhone execution is unavailable, report that truthfully; that limitation alone does not authorize fabricated evidence.

Commit the child implementation/evidence separately, publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CODEX_LOG_V01.md, verify remote visibility, and end the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Then continue to the next master-ordered child only if validations are green and no batch STOP condition exists.
