# PL-0158 Codex Implementation Log V01

## Scope and authority

- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`.
- Live tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
- Parent prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CODEX_PROMPT_V01.md
- Parent criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md
- Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0158_CODEX_PROMPT_V01.md
- Child criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0158_CHATGPT_AUDIT_CRITERIA_V01.md
- Mandatory architecture: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

The live tracker authorized M07-C001 / READY / CODEX for PL-0158 through PL-0165. The worktree was clean and 37 commits behind before a safe fast-forward to `67557ff28c38cd02630159ba34e2ae2472d5b94f`, the then-current `origin/main`.

## Implementation

PL-0158 records the selected COLMAP baseline in https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/engine_baseline.py and https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/M07_ENGINE_BASELINE.md.

- Selected version: COLMAP `3.12.6`.
- Source: https://github.com/colmap/colmap
- Release tag: https://github.com/colmap/colmap/tree/3.12.6
- Exact source revision: `4d5b60e19ad268072adaf1267d21fa38a9a828ca`.
- License provenance: https://colmap.github.io/license.html; COLMAP itself is recorded as New BSD / 3-clause BSD, with separate third-party dependency review required.
- Windows route: official release binaries or reproducible vcpkg/source build; PackLab discovers an external executable and does not bundle or auto-download it.
- Binary SHA-256 is explicitly unavailable because no COLMAP executable is installed on the builder host.
- The record makes no unsupported redistribution or license-clearance claim.

The deterministic focused test is https://github.com/Sekiph82/PackLab/blob/main/tests/core/test_engine_baseline.py. It asserts the exact version, release ref, source revision, license caveat and absence of an unobserved binary hash. No M06 authority, RAW_CAPTURE data, dependency lockfile, neural model, or future PL-0166+ implementation was changed.

## Validation

Focused test:

```text
uv run --locked pytest tests/core/test_engine_baseline.py -q -rs
1 passed
```

Static checks:

- `uv run --locked ruff check core/src/packlab_core/engine_baseline.py tests/core/test_engine_baseline.py` — passed.
- `uv run --locked mypy core/src/packlab_core/engine_baseline.py` — passed.
- `uv run --locked python -m compileall -q core/src/packlab_core/engine_baseline.py` — passed.
- `git diff --check` — passed.

Exact full locked suite:

```text
$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs
293 passed, 5 skipped, 1 deselected, 2 warnings in 23.86s
```

The five skips are the existing OpenCV-unavailable calibration skips plus the explicit Windows actual-symlink capability skip from https://github.com/Sekiph82/PackLab/blob/main/tests/studio/test_portability.py. The two warnings are pre-existing duplicate-zip warnings. No changed module has a reported type error.

## Publication

- Implementation/evidence commit: `0d836e56d80313f32e2f3c831cbc4976c5d3c3e3`, https://github.com/Sekiph82/PackLab/commit/0d836e56d80313f32e2f3c831cbc4976c5d3c3e3
- This child log is published in a separate log-only commit; its SHA is verified after publication.
- No TASKS.md or ChatGPT audit/criteria artifact was edited.
- Secrets, private scans, signing material, local caches, generated reconstruction intermediates and binaries were not added.
- This is builder evidence only; independent audit remains with ChatGPT.

READY_FOR_INDEPENDENT_AUDIT
