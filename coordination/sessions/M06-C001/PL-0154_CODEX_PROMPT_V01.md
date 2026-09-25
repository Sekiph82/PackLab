# PL-0154 — Codex Work Order V01

Task: **PL-0154 — Object selection and visibility model**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0154_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0154_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0154_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. Preserve accepted M03–M05 and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M07.

Use the single viewport backend/adapter selected by PL-0151. Display/debug/LOD/export representations must never overwrite authoritative source geometry.

## Mandatory implementation

1. Define stable scene object IDs/types for Scan Mesh, Design Model, cap, label and reference geometry with visible/selectable state.
2. Implement single-selection baseline plus programmatic clear/select and visibility toggles through one scene model; viewport widgets must reflect domain scene state rather than own it.
3. Selection of hidden/missing objects must fail or clear deterministically; raw source assets must never be modified.
4. Expose scene object changes to the object-tree/inspector UI seams created in M06 without starting later editing milestones.
5. Add tests for object registration, selection, hidden-object behavior, visibility persistence/state restore and duplicate-ID rejection.

## Validation

Use offscreen/headless tests where supported and truthfully record unavailable native/GPU capabilities. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Create one implementation/evidence commit and one separate log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
