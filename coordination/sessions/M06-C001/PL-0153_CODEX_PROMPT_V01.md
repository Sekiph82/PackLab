# PL-0153 — Codex Work Order V01

Task: **PL-0153 — World grid, axes and millimetre scale cues**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0153_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0153_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0153_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. Preserve accepted M03–M05 and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M07.

Use the single viewport backend/adapter selected by PL-0151. Display/debug/LOD/export representations must never overwrite authoritative source geometry.

## Mandatory implementation

1. Add viewport world grid, XYZ axes and millimetre-based scale cues consistent with PackLab's packaging/measurement coordinate conventions.
2. Grid spacing/labels must adapt to camera distance without changing underlying world units.
3. Expose visibility and scale-cue settings through the viewport state model so later Settings/workspace persistence can restore them.
4. Do not claim calibrated real-world accuracy here; this is a visual unit cue, with M09 owning measurement accuracy.
5. Add deterministic scene/state tests for axes orientation, mm unit metadata, adaptive grid spacing thresholds, visibility toggles and camera-distance changes.

## Validation

Use offscreen/headless tests where supported and truthfully record unavailable native/GPU capabilities. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Create one implementation/evidence commit and one separate log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
