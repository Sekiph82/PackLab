# PL-0186 — Codex Implementation Log V02

## Handoff

- Task: PL-0186 V02 — SAM 2.1 Hiera Base+ local PyTorch segmentation backend
- Session: M08-C001
- Required actor: CODEX
- Starting synchronized SHA: `6da4b0c`
- Implementation SHA: `ee3c15918271b78d758810dc7ac9080a553ae739`
- Tracking branch: `main`
- Remote: `origin/main`
- Final handoff state: runtime implementation complete; independent ChatGPT audit required

## Authorization and synchronization

Read before implementation:

- `coordination/sessions/M08-C001/PL-0186_CODEX_PROMPT_V02.md`
- `coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_CRITERIA_V02.md`
- `docs/architecture/adr/ADR-0004-sam2.1-segmentation-backend.md`
- `docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md`
- `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`

Commands and results:

- `git fetch origin main --prune` — completed.
- `git status --porcelain` — clean before implementation.
- `git rev-list --left-right --count HEAD...origin/main` — `0 6`; local checkout was behind and not diverged.
- `git merge --ff-only origin/main` — completed, advancing local `main` to `6da4b0c`.
- Live `TASKS.md` then reported M08 / M08-C001 / PL-0186 V02 / READY / CODEX and explicitly authorized PL-0186 while keeping PL-0187+ and M09 unauthorized.

## Architecture and implementation

`SAM21BasePlusBackend` implements the existing PackLab `SegmentationBackend` boundary. SAM-specific APIs remain in `core/src/packlab_core/sam21_backend.py`; downstream segmentation and geometry code continues to consume only PackLab contracts.

The runtime boundary is:

`SegmentationRequest -> SAM21BasePlusBackend -> SAM21Runtime -> normalized source-grid MaskArtifact`

The runtime is injected through a small local protocol for deterministic tests. The production adapter lazily imports local `torch`, `torchvision`, `sam2`, and `numpy` only when probing/executing. No hosted API, credential, network inference, or application-time download path exists. The image provider is explicit and receives a request; segmentation does not rewrite source bytes.

Implemented behavior:

- exact SAM 2.1 Hiera Base+ model/config/checkpoint identity;
- official checkpoint filename, byte-size and SHA-256 verification;
- fail-closed missing runtime/config/checkpoint/hash mismatch behavior;
- explicit native-Windows versus WSL, CPU and CUDA capability facts;
- point prompts and source-pixel bounds validation;
- box prompts normalized to SAM `xyxy` coordinates;
- source-grid coordinate metadata and transform round trip;
- boolean/numeric mask normalization, finite confidence bounds and dimension checks;
- immutable PackLab provenance and raw-model-output marking without PL-0187 post-processing;
- deterministic mask revision identity and source digest preservation.

The public contract gained structured `details` on capability reports and `runtime_details` on provenance. Existing fake-backend replacement behavior remains contract-compatible.

## Frozen model and checkpoint provenance

- Upstream repository: `https://github.com/facebookresearch/sam2`
- Reviewed source revision: `2b90b9f5ceec907a1c18123530e92e794ad901a4`
- Repository license: Apache-2.0
- Model: `sam2.1_hiera_base_plus.pt`
- Config: `configs/sam2.1/sam2.1_hiera_b+.yaml`
- Official source: `https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt`
- Acquired explicitly outside Git on 2026-10-01: `323606802` bytes
- SHA-256: `a2345aede8715ab1d5d31b4a509fb160c5a4af1970f199d9054ccfb746c004c5`
- Verification result: `verified: True`
- Repository status: checkpoint binary is not tracked or committed.

The expected hash and byte size are PackLab-owned constants in the adapter and the verified artifact identity is recorded in `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`. No PyTorch, torchvision, SAM 2 or NumPy package was present in the locked PackLab environment, so no native model execution claim is made.

## Runtime capability evidence

Probe command:

```text
uv run --locked python -c "from pathlib import Path; from packlab_core.sam21_backend import verify_sam21_checkpoint, PyTorchSAM21Runtime; p=Path(<explicit-temp-checkpoint>); print(verify_sam21_checkpoint(p).as_dict()); print(PyTorchSAM21Runtime(p, Path('configs/sam2.1/sam2.1_hiera_b+.yaml')).probe().as_dict())"
```

Actual runtime facts:

- Python: `3.12.10`
- Environment: `native-windows`
- PyTorch: unavailable / not importable
- torchvision: unavailable / not importable
- SAM 2: unavailable / not importable
- Device: unavailable
- CUDA: unavailable; no CUDA version claimed
- Backend execution: unavailable and fail-closed
- Network fallback: disabled

The fake/local runtime seam reports both CPU and CUDA capability shapes in tests without claiming that either device is installed in this environment. The real SAM runtime remains capability-probed and requires an explicitly configured local checkpoint and exact config.

## Changed files

- `core/src/packlab_core/sam21_backend.py`
- `core/src/packlab_core/segmentation.py`
- `tests/core/test_sam21_backend.py`
- `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`

No `TASKS.md`, ADR, ChatGPT audit/criteria file, accepted predecessor evidence, lockfile, checkpoint, private scan, credential, signing material or generated model artifact was changed.

## Validation

Focused PL-0186 and contract/regression commands:

- `uv run --locked pytest -q tests/core/test_sam21_backend.py tests/core/test_segmentation.py` — `17 passed`.
- `uv run --locked pytest -q tests/core/test_segmentation.py tests/core/test_segmentation_benchmark.py tests/packscan/test_object_mask_contract.py` — `21 passed`.
- Combined final focused command including all four suites — `29 passed`.
- `uv run --locked ruff check core/src/packlab_core/sam21_backend.py core/src/packlab_core/segmentation.py tests/core/test_sam21_backend.py` — passed.
- `uv run --locked ruff format --check core/src/packlab_core/sam21_backend.py core/src/packlab_core/segmentation.py tests/core/test_sam21_backend.py` — passed.
- `uv run --locked mypy core/src/packlab_core/sam21_backend.py core/src/packlab_core/segmentation.py` — passed.
- `uv run --locked python -m compileall -q core/src/packlab_core/sam21_backend.py core/src/packlab_core/segmentation.py tests/core/test_sam21_backend.py` — passed.
- `git diff --check` — passed.

Exact locked full suite:

- `uv run --locked pytest -q -rs` — `839 passed, 6 skipped, 1 deselected, 2 warnings`.
- Skips were existing unavailable `cv2` coverage and Windows symlink privilege coverage; warnings were existing duplicate ZIP-name warnings.

Repository-wide static checks:

- `uv run --locked mypy core/src apps/windows-studio/src tools` — 18 pre-existing errors in unchanged files: `transfer_protocol.py`, `calibration/marker_detection.py`, `packscan/container.py`, `packlab_studio/import_report.py`, and `packlab_studio/receiver.py`. The changed PL-0186 files passed targeted mypy.
- `uv run --locked ruff check .` — 2 pre-existing errors in unchanged `preview/windows/packlab_preview.py` (`tkinter.ttk` unused/import ordering).
- `uv run --locked ruff format --check .` — 71 existing files would be reformatted; none are PL-0186 changed files.
- `uv run --locked python -m compileall -q core/src apps/windows-studio/src tools tests` — passed.

Scope/privacy/dependency checks:

- Protected/scope review found only the four changed files listed above; `TASKS.md`, ChatGPT audit/criteria files, PL-0187+, M09 and `uv.lock` were untouched.
- No tracked model/binary artifact was added; `rg --files -g '*.pt' -g '*.pth' -g '*.bin' -g '*.onnx' -g '*.safetensors'` returned no repository model artifact.
- Source review found no secrets, tokens, credentials, private scans, signing material or hosted-service integration.
- The only new runtime provenance is the approved SAM 2.1 component boundary; PyTorch/torchvision/CUDA wheels were not added to the canonical lock.

## Publication

- Implementation/evidence commit created: `ee3c15918271b78d758810dc7ac9080a553ae739` (`Implement SAM 2.1 Hiera Base+ backend`).
- `git push origin main` — completed: `6da4b0c..ee3c159`.
- `git ls-remote origin refs/heads/main` — returned `ee3c15918271b78d758810dc7ac9080a553ae739`.
- This file is intentionally being published in a separate log-only commit.

PL-0187+ and M09 were not started. No audit verdict is assigned by Codex.

READY_FOR_INDEPENDENT_AUDIT
