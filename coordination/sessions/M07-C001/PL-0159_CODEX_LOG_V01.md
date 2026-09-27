# PL-0159 Codex Implementation Log V01

## Scope and authority

- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`.
- Live tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
- Parent prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CODEX_PROMPT_V01.md
- Parent criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md
- Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0159_CODEX_PROMPT_V01.md
- Child criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0159_CHATGPT_AUDIT_CRITERIA_V01.md
- Mandatory architecture: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

The preceding PL-0158 implementation/evidence and log commits were published before this child began. The worktree was clean and synchronized with `origin/main` at `46469d82fd4359cec8f6bdfe1cd7a82aa638b13a`.

## Implementation

PL-0159 extends the baseline record in https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/engine_baseline.py and https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/M07_ENGINE_BASELINE.md.

- Selected version: OpenMVS `2.4.0`.
- Source: https://github.com/cdcseacave/openMVS
- Release: https://github.com/cdcseacave/openMVS/releases/tag/v2.4.0
- Exact source revision: `58117204c86bbb11a0b25b26a8987676cf11274d`.
- License provenance: https://github.com/cdcseacave/openMVS/blob/v2.4.0/LICENSE; GNU AGPL-3.0 and explicit `HIGH LICENSE ATTENTION` classification.
- Windows route: official release Windows x64 assets or reproducible source build; PackLab discovers an external executable and does not bundle or auto-download it.
- Binary SHA-256 is explicitly unavailable because no OpenMVS executable is installed on the builder host.
- The record makes no distribution-clearance claim. Bundling, modification, linking, installer distribution and network/service deployment remain separate review gates.

The deterministic focused test is https://github.com/Sekiph82/PackLab/blob/main/tests/core/test_engine_baseline.py. An initial assertion used a lowercase wording check; the test exposed the mismatch, and the record was corrected to the explicit required uppercase classification before validation passed. No M06 authority, RAW_CAPTURE data, dependency lockfile, neural model, or future PL-0166+ implementation was changed.

## Validation

Focused test:

```text
uv run --locked pytest tests/core/test_engine_baseline.py -q -rs
2 passed
```

Static checks:

- `uv run --locked ruff check core/src/packlab_core/engine_baseline.py tests/core/test_engine_baseline.py` — passed.
- `uv run --locked mypy core/src/packlab_core/engine_baseline.py` — passed.
- `uv run --locked python -m compileall -q core/src/packlab_core/engine_baseline.py` — passed.
- `git diff --check` — passed.

Exact full locked suite:

```text
$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs
294 passed, 5 skipped, 1 deselected, 2 warnings in 22.63s
```

The five skips are the existing OpenCV-unavailable calibration skips plus the explicit Windows actual-symlink capability skip from https://github.com/Sekiph82/PackLab/blob/main/tests/studio/test_portability.py. The two warnings are pre-existing duplicate-zip warnings. No changed module has a reported type error.

## Publication

- Implementation/evidence commit: `c57cb1c7d707eea71389d7e3efa4951aa05e7d0f`, https://github.com/Sekiph82/PackLab/commit/c57cb1c7d707eea71389d7e3efa4951aa05e7d0f
- This child log is published in a separate log-only commit; its SHA is verified after publication.
- No TASKS.md or ChatGPT audit/criteria artifact was edited.
- Secrets, private scans, signing material, local caches, generated reconstruction intermediates and binaries were not added.
- This is builder evidence only; independent audit remains with ChatGPT.

READY_FOR_INDEPENDENT_AUDIT
