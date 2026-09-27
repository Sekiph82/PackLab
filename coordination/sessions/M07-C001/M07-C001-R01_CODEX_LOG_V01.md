# M07-C001-R01 — Codex Remediation Log V01

Date: 2026-09-27  
Repository: https://github.com/Sekiph82/PackLab  
Branch: `main`  
Cycle: `M07-C001-R01`  
Scope: **PL-0160 and PL-0161 only**

## Authorization and synchronization

- Read the authoritative tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
- Read the frozen prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CODEX_PROMPT_V01.md
- Read the frozen audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CHATGPT_AUDIT_CRITERIA_V01.md
- Read the mandatory architecture: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md
- Read the ADR: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0003-object-centric-reconstruction-authority.md
- Tracker authorized `M07-C001-R01`, `CHANGES_REQUIRED`, `CODEX`, remediation of PL-0160/PL-0161, with PL-0158/PL-0159 and PL-0162–PL-0165 accepted.
- `git fetch origin --no-tags` completed; the clean checkout fast-forwarded from `1b256d5c02a3f35abd90367ce6552a99ecb35036` to origin/main `d1d068cd01f8f29df409cd07e6a680d7f0cd54a4`.
- Final implementation commit was pushed and remote `origin/main` verified at `508e4f2f63aa2e45c62d4e3de33b79297b7ac2b5`.

## Root cause and implementation

The previous shared runner invoked every engine with unsupported `--version` semantics. The exact COLMAP 3.12.6 CLI supports `help`/help forms, while OpenMVS 2.4.0 applications expose help/no-input behavior and may return the expected non-zero status when no scene is supplied.

Changed files:

- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/engine_probe.py
- https://github.com/Sekiph82/PackLab/blob/main/tests/core/test_engine_probe.py

Implementation:

- Added `EngineProbePolicy` with explicit argv and accepted exit codes.
- COLMAP uses `help` and accepts exit code `0` only.
- OpenMVS uses `-h` and accepts exit code `1` only when the recognized `OpenMVS` banner parses successfully.
- Missing, launch failure, invalid/unparseable, unsupported, and valid states remain distinct.
- Added a PackLab-owned five-component OpenMVS report for InterfaceCOLMAP, DensifyPointCloud, ReconstructMesh, RefineMesh and TextureMesh. Readiness is false unless every component is valid.
- The component suite only probes executables; it does not launch reconstruction work, install binaries, download dependencies, scan arbitrary PATH locations, or execute shell strings.
- Preserved COLMAP 3.12.6, OpenMVS 2.4.0, M06 authorities, accepted PL-0158/PL-0159/PL-0162–PL-0165, and did not start PL-0166.

## Tests and checks

- Focused remediation tests: `10 passed`.
- Exact locked full suite: `321 passed, 5 skipped, 1 deselected`; 2 existing zipfile warnings.
- `uv run --locked ruff check .`: passed.
- Targeted format check for changed files: passed.
- Targeted mypy for `core/src/packlab_core/engine_probe.py`: passed, no issues.
- Compileall for core, Studio, tools and tests: passed.
- Project lint via `uv run --locked python tools/tasks.py lint`: passed.
- `git diff --check`: passed.
- Repository-wide format check reports 68 pre-existing unformatted files outside this remediation; no unrelated files were changed.
- Protected-file review: no TASKS.md, ChatGPT audit/criteria, `.github`, or `.hiveai` files changed.
- Dependency/lock review: no dependency or lock files changed.
- Secrets/privacy/signing/generated/binary review: no secrets, credentials, signing material, private scans, generated artifacts, or engine binaries added.

## Handoff

Implementation/evidence commit: `508e4f2f63aa2e45c62d4e3de33b79297b7ac2b5`  
Required next action: independent ChatGPT audit against the frozen criteria and actual GitHub state. Codex does not edit TASKS.md, write the ChatGPT audit, assign PASS, or start PL-0166.

READY_FOR_INDEPENDENT_AUDIT
