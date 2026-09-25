# PL-0156 — Codex Work Order V01

Task: **PL-0156 — Viewport screenshot/export preview**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0156_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0156_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0156_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. Preserve accepted M03–M05 and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M07.

Use the single viewport backend/adapter selected by PL-0151. Display/debug/LOD/export representations must never overwrite authoritative source geometry.

## Mandatory implementation

1. Add a viewport screenshot/export-preview service that captures the current camera/view state into a deterministic image file suitable for audit/report evidence.
2. Support explicit output path/format and include lightweight sidecar metadata for project/revision, camera state, visible object IDs and viewport backend/version without private absolute-path leakage.
3. Use atomic publication and never overwrite raw source evidence.
4. Handle headless/offscreen capture when supported by the chosen backend and report capability limitations truthfully.
5. Add tests for image creation, dimensions/non-empty output, sidecar metadata, atomic overwrite policy, redaction and unavailable-backend failure.

## Validation

Use offscreen/headless tests where supported and truthfully record unavailable native/GPU capabilities. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Create one implementation/evidence commit and one separate log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
