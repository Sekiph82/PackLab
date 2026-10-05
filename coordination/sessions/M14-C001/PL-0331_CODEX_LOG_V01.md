# PL-0331 - Codex Implementation Log V01

Task: **Record render settings and Blender version for reproducibility**

Cycle: **M14-C001-R03**

Prompt: `PL-0331_CODEX_PROMPT_V01.md`

Audit criteria: `PL-0331_CHATGPT_AUDIT_CRITERIA_V01.md`

## Authorization and source reads

- Live root `TASKS.md` authorized PL-0331 as the final ordered child in M14-C001-R03. PL-0330 evidence and its separate log had been published before PL-0331 began. M15+ remained unauthorized. Root `TASKS.md` was not edited.
- Read PL-0331 prompt/criteria; exact predecessor PL-0330 prompt/criteria and implementation; PL-0329 through PL-0326 prompts/criteria and relevant implementations; M13 final audit; M09 physical-validation deferral; ADR-0005; and the M14 authority rules.
- Execution checkout: `C:\Users\sekip\.codex\worktrees\packlab-m13-c001\PackLab`, branch `codex/m13-c001-pl0297`, origin `https://github.com/Sekiph82/PackLab.git`. Protected Desktop checkout preserved.
- Synchronized starting SHA: `752279b736969767c02df20e7bff74b8ae4b2510`; zero divergence from fetched `origin/main` before implementation.

## Implementation

Implementation/evidence commit: `fb438304c9cb705609d135b67f8ddafd98f2d046` (`Add canonical M14 render provenance`).

Changed files:

- `core/src/packlab_core/blender_render_provenance.py` — one deterministic M14 provenance schema shared by still and GLB artifacts. It binds PackLab commit/version, Blender executable SHA-256 and version/build, scene-package revision/digest, source revisions/digests, engine/device/settings, camera/light preset IDs and output digests. Identity excludes output paths and timestamps; relative output paths remain in the evidence portion of the record. It rejects absolute paths and invalid revision/digest fields and carries explicit limitations, including no cross-hardware pixel identity guarantee and no physical, material, regulatory, manufacturing or production authority escalation.
- `core/src/packlab_core/blender_render.py` — adds the shared record to the standard-view aggregate and each still evidence sidecar, including the three output digests and camera/light preset revisions. Blender executable SHA is computed from the actual executable; PackLab build identity must be supplied explicitly.
- `core/src/packlab_core/blender_glb_export.py` — adds the same schema to the GLB sidecar, with the exporter settings, actual executable SHA and validated output digest/length. The export device is explicitly marked not applicable and the artifact has no camera/light presets because cameras and lights are excluded from the GLB.
- `tests/core/test_blender_render_provenance.py` — deterministic identity, output/build binding, path exclusion, malformed input and authority-limitation coverage.
- `tests/core/test_blender_render_batch.py` and `tests/core/test_blender_glb_export.py` — integration assertions for aggregate/per-still/GLB records and real build/output bindings.

For EEVEE, the selected device is recorded as `EEVEE_DEFAULT`; the record does not claim that different hardware will produce pixel-identical images. Source coordinate authority and the prior physical-validation deferral remain intact.

## Validation

Expected success: all still and GLB records use the same canonical contract and bind the exact PackLab/Blender build, source package, source revisions, settings/presets and artifact digests; identity is deterministic and path/timestamp independent; no ambient paths or authority upgrades appear. Real Blender still and GLB smokes are mandatory evidence for their respective outputs.

- Focused unit/regression run: `uv run --locked pytest tests/core/test_blender_render_provenance.py tests/core/test_blender_render_batch.py tests/core/test_blender_glb_export.py -q` — **12 passed, 2 skipped** (opt-in real capability cases).
- Real still+GLB run: `$env:PACKLAB_REAL_BLENDER_SMOKE='1'; uv run --locked pytest tests/core/test_blender_render_provenance.py tests/core/test_blender_render_batch.py tests/core/test_blender_glb_export.py -q -s` — **14 passed**, including the three-view actual render and actual GLB export.
- Exact Blender executable: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`; Blender **5.2.2 LTS**, version `[5,2,2]`, build hash `d13f752e3b9c`, branch `blender-v5.2-release`, date `2026-09-15`; executable SHA-256 `f141a3c5754500e6f84361099a4cd53f0bb7662b6a0d2cfaaa8fbb63e92234a0`.
- Exact PackLab identity in both real records: version `0.1.0`, commit `fb438304c9cb705609d135b67f8ddafd98f2d046`.
- Still record identity: `m14-render-provenance:f15b07574bd2c10b7c010a1dcbd6e57bdb8d53031f003fc44fdc7ad207a8b65f`. Engine `BLENDER_EEVEE`, device `EEVEE_DEFAULT`, 256×256 PNG RGBA, 8 samples, Standard view transform. Output SHA-256 values:
  - FRONT: `f47c378a0f14bb895f69ce25cf71a1ed41773e3dcd5ed11d7647a9ea637b9da3` (13,780 bytes)
  - THREE_QUARTER: `5239206d4187b18f672207a182ceeb9937a9d1f588b50085c5db1d9f56f1c496` (14,906 bytes)
  - BACK: `2860f8c5df7a30a0fd72afcc056510fdbbc6f506609dfe73a41f1f6fe2977647` (13,780 bytes)
- The still provenance lists all three camera/light preset revisions and is byte-identical in the aggregate manifest and each per-view render evidence sidecar. Its source authority retains `mm_unverified` and `DEFERRED_OWNER_VALIDATION`.
- GLB record identity: `m14-render-provenance:d019731267e8e52a7a2efdb8667bdc6f807ff86c2f007287b0a23acb62ff8c98`. Engine `BLENDER_GLTF_EXPORTER`; device `NOT_APPLICABLE_EXPORT_ONLY`; actual GLB SHA-256 `9734def46557780899e690710a7a9a27bea71cf94e58788d83faee0b6400eda7` (18,464 bytes). GLB retained 5 materials, 3 textures, 1 embedded image, 0 external URIs. Both actual records excluded the pytest temporary root.
- The provenance unit tests changed only the relative output path and verified identity remained stable; changing the output digest or PackLab commit changed identity. Absolute output paths are rejected. Timestamp data is not an input to the canonical record.
- Full locked suite: `uv run --locked pytest` — **1,867 passed, 11 skipped, 1 deselected, 2 existing duplicate ZIP-name warnings** in 79.55 s.
- Ruff: `uv run --locked ruff format --check` and `uv run --locked ruff check` over all six changed files — passed; all six formatted.
- Targeted mypy: `uv run --locked mypy --follow-imports=silent core/src/packlab_core/blender_render.py core/src/packlab_core/blender_glb_export.py core/src/packlab_core/blender_render_provenance.py` — no issues in 3 source files.
- Compile: `uv run --locked python -m compileall -q` over all six changed files — passed.
- Dependency/lock: `uv lock --check` — 78 packages resolved; no dependency or lockfile changes.
- Scope/privacy/security: no tracker edits, private evidence, absolute paths in actual records, network/download code, added dependency, Blender binary, or later-child/M15 work. Export/render remain offline and derived. `git diff --check` and staged check passed.

## Publication

- Implementation/evidence commit pushed to authorized `origin/main`: `fb438304c9cb705609d135b67f8ddafd98f2d046`.
- At implementation publication verification, local `HEAD`, fetched `origin/main`, and `git ls-remote origin refs/heads/main` all equaled `fb438304c9cb705609d135b67f8ddafd98f2d046`; divergence was `0 0` and worktree clean.
- This is builder evidence only; independent audit acceptance is not asserted. The separate log-only commit and final R03 handoff parity are recorded in the M14 master index and continuation update following this log.

READY_FOR_INDEPENDENT_AUDIT
