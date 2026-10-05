# PL-0324 - Codex Implementation Log V01

Task: **Integrate Blender headless executable discovery and version probe**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0324_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0324_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Live root `TASKS.md` authorizes `M14-C001-R02`: PL-0313 V02 followed by PL-0314 through PL-0331; actor `CODEX`. The tracker was not edited. PL-0324 remains the real Blender capability gate; M15+ remains unauthorized.
- Read the live `TASKS.md`, M14 R02 continuation prompt and criteria, M14 partial audit V02, M13 R02 final audit, M09 physical-validation deferral, ADR-0005, the PL-0323 predecessor prompt/criteria, and this PL-0324 prompt/criteria before implementation.
- Starting synchronized SHA: `4a8a8399acf79383851a52159a8aab530a80e271`; worktree clean on `codex/m13-c001-pl0297`, push target `origin/main`. The protected Desktop checkout remains untouched.
- Implementation/evidence commit: `35e8f64895925864280096fcd66052ed06a91434` (`Probe Blender headless capability safely`), pushed to `origin/main`.

## Implementation

Added `core/src/packlab_core/blender_capability.py` with deterministic discovery precedence: an explicit configured path is authoritative; otherwise discovery checks `PATH` and fixed platform-standard locations. An invalid configured path does not silently fall back. The adapter never scans arbitrary drives, downloads, or installs Blender.

The probe launches Blender through an argv list with `shell=False`, stdin closed, a 20-second timeout, background mode, factory startup, auto-execution disabled, and a fixed Python expression that reads only Blender build facts. It returns `READY`, `UNAVAILABLE`, or `INCOMPATIBLE`, including version, build hash, branch, build date, generic discovery source and bounded reason code. It excludes the executable path and raw process output from diagnostics. The supported-version policy is Blender major version 5; all other majors report `INCOMPATIBLE`.

Integrated this probe with the existing generic `discover_capabilities` registry. Its legacy status maps READY to AVAILABLE, UNAVAILABLE to UNAVAILABLE and INCOMPATIBLE to UNKNOWN while preserving the specialized diagnostic in `detail`.

Real local capability evidence:

- Headless discovery/probe: `READY`, version `5.2.2 LTS`, build hash `d13f752e3b9c`, branch `blender-v5.2-release`, build date `2026-09-15`, discovery source `platform-standard`.
- `uv run python -c "from packlab_core.blender_capability import discover_blender; print(discover_blender().as_dict())"` returned the facts above without an executable path.
- Real headless smoke: Blender `--background --factory-startup --python-expr` successfully imported `bpy` and returned version/hash/branch facts. The automated real-probe test also passed during the focused and full test runs.

Files changed:

- `core/src/packlab_core/blender_capability.py`
- `core/src/packlab_core/capabilities.py`
- `tests/core/test_blender_capability.py`
- `tests/core/test_capabilities.py`

No Blender binary, dependency, lockfile, tracker, audit artifact, later-child, or M15+ file was changed.

## Validation

| Command/check | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run pytest tests/core/test_blender_capability.py tests/core/test_capabilities.py -q` | Configured path, missing path, non-executable/wrong binary, timeout, version parsing/policy, PATH/platform discovery, argv safety, privacy and real smoke are covered. | PASS: 18 passed in 1.77s, including the real local Blender headless build probe. |
| `uv run --locked pytest -q` | Locked repository suite passes; any failure blocks this child. | PASS: 1,816 passed, 6 skipped, 1 deselected in 175.68s. Two existing duplicate ZIP-name warnings in container-validation tests. |
| `uv run ruff check core/src/packlab_core/blender_capability.py core/src/packlab_core/capabilities.py tests/core/test_blender_capability.py tests/core/test_capabilities.py` | Changed files pass Ruff. | PASS: all checks passed. |
| `uv run ruff format --check core/src/packlab_core/blender_capability.py core/src/packlab_core/capabilities.py tests/core/test_blender_capability.py tests/core/test_capabilities.py` | Changed files are formatted. | PASS: all four files formatted. |
| `uv run mypy --follow-imports=silent core/src/packlab_core/blender_capability.py core/src/packlab_core/capabilities.py` | Changed sources pass targeted typing. | PASS: no issues in 2 source files. |
| `uv run python -m compileall -q core/src/packlab_core/blender_capability.py core/src/packlab_core/capabilities.py tests/core/test_blender_capability.py tests/core/test_capabilities.py` | Changed source and tests compile. | PASS. |
| `uv lock --check`; `git diff -- TASKS.md pyproject.toml uv.lock` | No dependency/lockfile or tracker change. | PASS: 78 packages resolved; no protected-file diff. |
| `git diff --check`; changed-file privacy/security/scope review | No whitespace, network/download/install, path leakage, or scope leakage. | PASS. Probe uses no network API or installation path. Subprocess receives a fixed argument vector with `shell=False`; timeout and stdin are bounded. Diagnostics exclude absolute paths and raw output. |
| Real Blender capability smoke | An approved executable must launch headlessly and expose usable version/build facts; fakes cannot substitute. | PASS: installed Blender `5.2.2 LTS` launched in background/factory mode; `bpy` returned build hash `d13f752e3b9c`, branch `blender-v5.2-release`, build date `2026-09-15`. |
| `git fetch origin main`; `git rev-list --left-right --count HEAD...origin/main`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git ls-remote origin refs/heads/main` | Starting source synchronized and published implementation matches canonical GitHub `main`. | PASS at implementation SHA `35e8f64895925864280096fcd66052ed06a91434`; divergence before implementation was `0 0`; pushed `HEAD:main`; local HEAD, fetched `origin/main`, and live GitHub ref equal. |

## Limitations

- Supported executable policy is Blender 5.x. Other major versions are conservatively `INCOMPATIBLE` until separately authorized and validated.
- The real check proves headless process startup and `bpy` build-fact access. It does not claim a scene render/export result, dimensional accuracy, print fit, material certification, manufacturing suitability, regulatory approval, or physical accuracy.
- Blender remains an external installation. No binary is bundled, committed, or automatically installed.

## Handoff

PL-0324 V01 implementation/evidence is builder-green and published. Its matching log is published separately and ends with the required marker. No independent audit verdict is claimed. Continue at PL-0325 only after this child log/index publication and remote parity verification.

READY_FOR_INDEPENDENT_AUDIT
