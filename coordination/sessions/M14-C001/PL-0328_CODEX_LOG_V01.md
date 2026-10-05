# PL-0328 - Codex Implementation Log V01

Task: **Render transparent-background product image**

Cycle: **M14-C001-R03**

Prompt: `PL-0328_CODEX_PROMPT_V01.md`

Audit criteria: `PL-0328_CHATGPT_AUDIT_CRITERIA_V01.md`

## Authorization and source reads

- Live root `TASKS.md` authorized the M14-C001-R03 ordered batch. PL-0327 builder evidence and its separate log had been published before PL-0328 started. PL-0328 was active; PL-0329 through PL-0331 remained frozen. Root `TASKS.md` was not edited.
- Read the PL-0328 prompt/criteria, PL-0327 preset prompt/criteria and implementation, PL-0326 scene package/prompt/criteria, M13 final audit, M09 physical-validation deferral, ADR-0005, and the M14 authority rules.
- Execution checkout: `C:\Users\sekip\.codex\worktrees\packlab-m13-c001\PackLab`, branch `codex/m13-c001-pl0297`, origin `https://github.com/Sekiph82/PackLab.git`. Protected Desktop checkout preserved.
- Synchronized starting SHA: `bc7c7710ecaff480684211b4aafe832c802cbae8`; zero divergence from fetched `origin/main` before implementation.
- M15+ remains unauthorized and was not started.

## Implementation

Implementation/evidence commit: `60c7c73cc141ac8a87d8e7a46a8dfd5fc5d1990c` (`Render transparent Blender product images for PL-0328`).

Changed files:

- `core/src/packlab_core/blender_render.py` — deterministic fixed render-stage composition over the validated PL-0326 scene package and PL-0327 preset; bounded render dimensions/samples/timeouts and project-relative outputs; offline Blender invocation; fixed EEVEE PNG/RGBA configuration; semantic render checks; path-free evidence manifest with source/package/preset/output digests and authority flags; generic failure/timeout handling.
- `core/src/packlab_core/blender_render_preset.py` — corrected the preset framing margin to the contract value `1.2`; the render job resolves its final view direction against the imported scene’s actual world-space bounds.
- `tests/core/test_blender_render.py` — deterministic/static job checks, bounded settings, failure/timeout/missing-result checks, and actual Blender transparent product render smoke.

The render stage accepts only the fixed PackLab scene runner and refuses a substituted scene script. It derives final camera target/distance and scaled studio light placement from imported mesh world bounds while retaining the selected preset direction and framing margin. It uses Blender **`BLENDER_EEVEE`**, fixed output dimensions/samples, PNG RGBA, 8-bit depth, transparent film, and Standard view transform. The PNG is reopened in Blender and checked for dimensions, alpha channel, visible pixels and transparent pixels; the render evidence SHA-256 is recomputed from file bytes. Blender process failures, timeouts and missing semantic-success markers fail closed.

Output/settings provenance is reproducible; pixel bytes are not claimed to be identical across hardware. The output and evidence paths are project-relative. The evidence manifest contains no temporary absolute paths. Render output remains derived presentation; there is no Design Model/CAD/Label Zone/material authority mutation, physical measurement inference, package-fit/print/manufacturing/certification/regulatory claim, network access, or download.

## Validation

Expected success was clean deterministic input validation, zero-returning Blender with a semantic-valid marker, RGBA/non-empty output matching the requested dimensions, both visible and transparent pixels, valid provenance/digests, and no authority/path leakage. Invalid bounds/settings/assets, process failure/timeout, malformed or clipped output, missing marker, or privacy/scope matches were failure conditions.

- Focused with both PL-0328 and PL-0327 render-preset tests: `$env:PACKLAB_REAL_BLENDER_SMOKE='1'; uv run --locked pytest tests/core/test_blender_render.py tests/core/test_blender_render_preset.py -q -s` — **24 passed**, including actual Blender camera/preset smoke and actual product render.
- Actual image: **256 × 256**, PNG color type 6 / RGBA, **14,906 bytes**, Blender alpha inspection: **44,048 transparent samples** and **22,599 visible samples**. Evidence SHA-256 matched file bytes: `8670087c69ada04f1f745b90204be9981b55685136091a0314e2428c13a21ef7`.
- Actual render settings: Blender `BLENDER_EEVEE`, 8 render samples, 100% resolution, transparent film, PNG RGBA/8-bit, Standard view transform, THREE_QUARTER framing. Camera framing check passed for all imported base-mesh bounds.
- Exact executable: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`; Blender **5.2.2 LTS**, version `[5,2,2]`, build hash `d13f752e3b9c`, branch `blender-v5.2-release`, date `2026-09-15`.
- Full locked suite: `uv run --locked pytest -q` — **1855 passed, 9 skipped, 1 deselected, 2 existing duplicate ZIP-name warnings** in 77.46 s.
- Ruff check and format check on four changed production/test files — passed; all four formatted.
- Targeted mypy: `uv run --locked mypy --follow-imports=silent core/src/packlab_core/blender_render.py core/src/packlab_core/blender_render_preset.py` — no issues in 2 source files.
- Lock/dependency: `uv lock --check` — 78 packages resolved; no lockfile changes.
- Compile: `uv run --locked python -m compileall -q core/src/packlab_core/blender_render_preset.py core/src/packlab_core/blender_render.py` — passed.
- Whitespace: `git diff --check` — passed. Privacy/security scan for `requests|urllib|socket|https?://|exec(|eval(` in render modules — no matches. `TASKS.md` diff empty.
- Initial real smoke surfaced that Blender 5.2.2 exposes the EEVEE engine as `BLENDER_EEVEE`; the runner was corrected and the real scene render then passed. The runner also requires its semantic-success marker because Blender can return process code zero after a script traceback.

## Publication

- Implementation/evidence commit pushed to `origin/main`: `60c7c73cc141ac8a87d8e7a46a8dfd5fc5d1990c`.
- At implementation publication verification: local `HEAD`, fetched `origin/main`, and `git ls-remote origin refs/heads/main` all equaled `60c7c73cc141ac8a87d8e7a46a8dfd5fc5d1990c`.
- The separate log-only commit and current final parity are recorded in the M14 R03 continuation/index update following this log.
- This is builder evidence only; independent audit acceptance is not asserted. The authorized batch proceeds to PL-0329.

READY_FOR_INDEPENDENT_AUDIT
