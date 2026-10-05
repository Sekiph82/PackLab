# PL-0327 - Codex Implementation Log V01

Task: **Create standard studio-lighting/camera presets for packaging mockups**

Cycle: **M14-C001-R03**

Prompt: `PL-0327_CODEX_PROMPT_V01.md`

Audit criteria: `PL-0327_CHATGPT_AUDIT_CRITERIA_V01.md`

## Authorization and source reads

- Live root `TASKS.md` authorized the M14-C001-R03 ordered batch. PL-0326 V02 had builder-green evidence and was published before PL-0327 began. PL-0327 was the active child; PL-0328 through PL-0331 remained frozen. Root `TASKS.md` was not edited.
- Read the PL-0327 prompt and criteria, PL-0326 V02 prompt/criteria and implementation, M13 final audit, M09 physical-validation deferral, ADR-0005, and M14 authority rules. Existing PL-0310…0325 authority/audit reads and R03 authorization are recorded in the M14 continuation log.
- Execution checkout: `C:\Users\sekip\.codex\worktrees\packlab-m13-c001\PackLab`, branch `codex/m13-c001-pl0297`, origin `https://github.com/Sekiph82/PackLab.git`. Protected Desktop checkout preserved.
- Synchronized starting SHA: `ac3a520cf9e60893c1b62931557e02dd5bc1440a`; zero divergence from fetched `origin/main` before implementation.
- M15+ remains unauthorized and was not started.

## Implementation

Implementation/evidence commit: `35b79489d1c94b00cfbeea63cdbaa369f90b1be5` (`Add deterministic Blender studio render presets for PL-0327`).

Changed files:

- `core/src/packlab_core/blender_render_preset.py` — immutable v1 named FRONT, THREE_QUARTER and BACK preset contract; deterministic bounds-centered perspective framing; bounded source bounds and background colors; fixed KEY/FILL/RIM area-light metadata; transparent and opaque background settings; exact source revision retention; stable content-derived revision identity; fixed data-only Blender scene runner.
- `tests/core/test_blender_render_preset.py` — named contract and stable-ID checks, all three camera directions, bounds/framing, lighting, transparent/opaque compatibility, finite/bounded input rejection, script privacy checks, and real Blender scene smoke.

Presets are `DERIVED_PRESENTATION_ONLY`; output explicitly records `physical_measurement_inference=false`. The runner starts from Blender factory scene but removes its default objects, creates one camera and exactly three preset area lights, applies transparent/world background settings and 1024x1024 framing, and emits path-free result facts. It does not render or modify Design Model/CAD/Label Zone/artwork/material authority. No dependency, Blender binary, ambient path identity or network path was added.

## Validation

For each gate, expected success was a zero exit / asserted deterministic scene facts; failure conditions were invalid/unbounded values accepted, inconsistent output, Blender process failure, failed assertions, or forbidden source matches.

- Focused: `uv run --locked pytest tests/core/test_blender_render_preset.py -q` — **14 passed, 1 skipped** (opt-in real Blender test intentionally skipped in this invocation).
- Real Blender: `$env:PACKLAB_REAL_BLENDER_SMOKE='1'; uv run --locked pytest tests/core/test_blender_render_preset.py -q -s` — **15 passed**. Actual camera/light/background setup succeeded in the approved headless executable, and output preserved source revisions without ambient path data.
- Exact executable: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`; Blender **5.2.2 LTS**, version `[5,2,2]`, build hash `d13f752e3b9c`, branch `blender-v5.2-release`, date `2026-09-15`.
- Full locked suite: `uv run --locked pytest -q` — **1847 passed, 8 skipped, 1 deselected, 2 existing duplicate ZIP-name warnings** in 91.06 s.
- Ruff check and format check on both changed files — passed; 2 files formatted.
- Targeted mypy: `uv run --locked mypy --follow-imports=silent core/src/packlab_core/blender_render_preset.py` — no issues in 1 source file.
- Lock/dependency: `uv lock --check` — 78 packages resolved, no lockfile changes.
- Compile: `uv run --locked python -m compileall -q core/src/packlab_core/blender_render_preset.py` — passed.
- Scope/privacy scan `requests|urllib|socket|https?://|exec(|eval(` in production preset module — no matches. Git whitespace checks passed. `TASKS.md` diff empty.
- During development the first real smoke exposed Blender factory startup's default light in the scene. The fixed runner now removes factory objects before applying the exact preset; the rerun proved the expected three-light result. Initial lint/type/test findings were corrected and all final gates passed.

## Publication

- Implementation/evidence commit pushed to `origin/main`: `35b79489d1c94b00cfbeea63cdbaa369f90b1be5`.
- At implementation publication verification: local `HEAD`, fetched `origin/main`, and `git ls-remote origin refs/heads/main` all equaled `35b79489d1c94b00cfbeea63cdbaa369f90b1be5`.
- The separate log-only commit and current final parity are recorded in the M14 R03 continuation/index update following this log.
- This is builder evidence only; independent audit acceptance is not asserted. The authorized continuation proceeds to PL-0328.

READY_FOR_INDEPENDENT_AUDIT
