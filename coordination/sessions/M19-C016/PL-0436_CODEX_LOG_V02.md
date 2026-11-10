# PL-0436 Codex Log V02 — VGGT Neural Backend Adapter Contract

Date: 2026-10-23 (Europe/Istanbul)

## Starting state and authorization

- Starting commit: `f8745047063aca6c17378ecb33604e6e1e5b5f02` (`main`).
- Final commit: `f8745047063aca6c17378ecb33604e6e1e5b5f02`; all changes remain local and uncommitted.
- Synchronization: `origin/main` fetched earlier in this run; local `HEAD` equals `origin/main` at the starting commit. Existing owner/local edits were preserved.
- Prompt and criteria: `PL-0436_CODEX_PROMPT_V02.md`, `PL-0436_VALIDATION_CRITERIA_V02.md`; mandatory `docs/implementation/PL-0436_COMMERCIAL_NEURAL_RECONSTRUCTION_RESEARCH.md` read in full.
- V02 makes the named VGGT family/checkpoint the integration target from the mandatory pre-read. Subsequent direct owner messages confirmed VGGT/Hugging Face access approval and explicitly asked Codex to continue the checkpoint work. This owner authorization supersedes V02's earlier no-download boundary for the one pinned checkpoint only; it does not authorize runtime activation before the remaining runtime/deployment gates are recorded. Hugging Face is not made a PackLab runtime dependency.

## Implementation

- Added `NEURAL_EXPERIMENTAL` to the common reconstruction backend identifiers.
- Added a VGGT-specific PackLab adapter boundary with no VGGT import, loader, network access, or runtime construction. It accepts only an injected runtime and a complete activation record for the exact `facebook/VGGT-1B-Commercial` identity and SHA-256.
- Default/incomplete activation fails closed during capability probe and execution. Runtime errors expose only exception type, not local paths or raw exception text.
- Normalized runtime output is checked for backend, project, source digest and non-metric-verified scale. Cancellation before inference is honored. Provenance contains checkpoint identity/hash only when the activation record is complete and contains no local model path or credential.
- Hardened the adapter so injected runtime metadata cannot supply the portable model build/license identity or elevate output authority. The adapter emits a fixed adapter version, pinned checkpoint identity/hash, restricted license identifier, and `RECONSTRUCTION_OBSERVATION` authority.
- Restricted portable license identifiers to path-free tokens. Evidence references remain opaque and are not emitted into portable output provenance.
- Pinned activation to the official model repository revision `ebb29a532abe92960eeb6903a5530f16990ef4ab` and `model.safetensors` metadata SHA-256 `2b766b284359bc47ce26be107254621f685b758a0282082ff109f3ff02788b53`; a different hash or revision fails closed. The remote hash is not yet locally verified because the gated file could not be fetched.
- Added synthetic-only contract tests. Their fake acceptance record is test data, not owner approval.

## Owner access update and checkpoint/runtime review

- Owner stated that VGGT access permission was granted. On 2026-10-23, `hf auth whoami` returned `user=Sekiph82`; no token value was read or exposed. The CLI downloaded only the pinned `model.safetensors` file into `%LOCALAPPDATA%\PackLab\models\VGGT-1B-Commercial`, outside the repository.
- Read the [official VGGT license](https://github.com/facebookresearch/vggt/blob/main/LICENSE.txt) and the upstream repository at pinned source commit `a288dd0f14786c93483e45524328726ab7b1b4ce`. The commercial checkpoint is under the VGGT AUP license; it permits use and redistribution subject to its agreement, and requires a copy of the agreement when research materials are distributed. Its prohibited-use terms include military/warfare/nuclear/espionage/ITAR and critical-infrastructure/transport/heavy-machinery activity. This records source terms, not a legal determination for every PackLab deployment.
- The [official Hugging Face model metadata](https://huggingface.co/facebook/VGGT-1B-Commercial) reports repo revision `ebb29a532abe92960eeb6903a5530f16990ef4ab`. The selected `model.safetensors` entry is 5,026,367,224 bytes with metadata SHA-256 `2b766b284359bc47ce26be107254621f685b758a0282082ff109f3ff02788b53`. The alternative `vggt_1B_commercial.pt` is 5,026,903,832 bytes and its card reports pickle imports; it was not downloaded. The selected local file is exactly 5,026,367,224 bytes and `Get-FileHash -Algorithm SHA256` returned `2b766b284359bc47ce26be107254621f685b758a0282082ff109f3ff02788b53`.
- The pinned source `requirements.txt` lists torch 2.3.1, torchvision 0.18.1, NumPy 1.26.1, Pillow, huggingface_hub, einops and safetensors; `pyproject.toml` additionally lists opencv-python. Direct project licenses reviewed from upstream sources: PyTorch BSD-style (its wheel includes additional third-party notices), torchvision BSD-3-Clause, NumPy BSD-3-Clause (wheels bundle additional libraries/notices), Pillow MIT-CMU, Hugging Face Hub Apache-2.0, einops MIT, safetensors Apache-2.0, OpenCV Apache-2.0. The opencv-python wheel additionally bundles FFmpeg under LGPL-2.1 and other third-party components. Exact resolved runtime versions and wheel-bundled notices remain to be captured before packaging/distribution.
- Installed `huggingface_hub==2.2.0` (including its `hf` CLI) into the existing PackLab `.venv`; the owner completed local authentication. No token value was read or exposed. An earlier unauthenticated `HEAD` request returned HTTP 401; authenticated download later succeeded. The model was saved to `%LOCALAPPDATA%\PackLab\models\VGGT-1B-Commercial`, not the repository or a shared cache.
- C: free space was 103,031,566,336 bytes before download and 97,761,771,520 bytes after it, a net decrease of 5,269,794,816 bytes while the 5,026,367,224-byte model file was added. This is an observed free-space delta, not a claim that all delta bytes are model allocation. Environment: Windows, Python 3.12.10, 16,870,006,784 bytes physical RAM, and `nvidia-smi` unavailable. The PackLab `.venv` initially lacked torch/torchvision/safetensors; an isolated CPU runtime was prepared later as recorded below.

## Local CPU runtime preparation

- Following the owner's direction to finish the VGGT task, prepared an isolated runtime environment under `%LOCALAPPDATA%\PackLab\venvs\vggt-cpu`; it is outside the PackLab repository and does not replace the project `.venv`.
- Installed exact runtime packages: torch 2.3.1+cpu, torchvision 0.18.1+cpu, NumPy 1.26.1, Pillow 10.4.0, huggingface_hub 2.2.0, einops 0.8.1, safetensors 0.6.2 and opencv-python 4.10.0.84. Resolved CPU dependencies include MKL 2021.4.0, Intel OpenMP 2021.4.0 and TBB 2021.13.1.
- Cloned official VGGT source into `%LOCALAPPDATA%\PackLab\src\vggt` at exact commit `a288dd0f14786c93483e45524328726ab7b1b4ce`; checkout is detached and clean. The checkpoint remains separately stored at `%LOCALAPPDATA%\PackLab\models\VGGT-1B-Commercial`.
- Runtime environment check: `python -m pip check` reported no broken requirements. Import smoke reported the exact versions above and `torch.cuda.is_available() == False`. No checkpoint weights were opened or executed.
- First-pass package notice inventory found license/notice materials for torch, torchvision, NumPy, Pillow, Hugging Face Hub, einops, safetensors, OpenCV and the MKL/OpenMP/TBB runtime packages. Full bundled-notice completeness and any end-user redistribution bundle remain unreviewed; this evidence does not authorize packaging or redistribution.
- C: free space was 97,761,771,520 bytes before isolated runtime/source preparation and 94,850,949,120 bytes afterward. This is an observed net decrease of 2,910,822,400 bytes; it is not attributed solely to the downloaded wheels or source checkout.
- The runtime has not been wired into the common backend or run on images. `ReconstructionInputSet` carries relative asset IDs and digests, but this contract has no image-asset resolver or output workspace writer; those interfaces and camera-coordinate normalization must be implemented and validated before real inference can produce PackLab manifests safely.

## Files changed for this task

- `TASKS.md`
- `coordination/sessions/M19-C016/PL-0436_CODEX_PROMPT_V02.md`
- `coordination/sessions/M19-C016/PL-0436_VALIDATION_CRITERIA_V02.md`
- `coordination/sessions/M19-C016/PL-0436_CODEX_LOG_V02.md`
- `core/src/packlab_core/reconstruction.py`
- `core/src/packlab_core/neural_reconstruction.py`
- `tests/core/test_neural_reconstruction_backend.py`
- `project-control/codex/jobs/PL-0436/job.json` (to be updated with this log's hash)

## Validation

1. Command: `.\.venv\Scripts\python.exe -B -m pytest -q tests/core/test_neural_reconstruction_backend.py tests/core/test_reconstruction.py`
   - Expected: focused VGGT adapter and shared-contract tests pass; nonzero exit means validation failure.
   - Actual: **14 passed in 0.12s** (exit 0).
   - Coverage: unavailable-by-default fail-closed behavior, protocol conformance, synthetic runtime normalization/provenance, immutable source identity, wrong-backend rejection, invalid checkpoint identity/hash, path-like license ID rejection, runtime metadata/authority normalization, each independent terms/review gate failing closed, and pre-inference cancellation.
2. Command: `.\.venv\Scripts\ruff.exe check core/src/packlab_core/reconstruction.py core/src/packlab_core/neural_reconstruction.py tests/core/test_neural_reconstruction_backend.py`
   - Expected: no lint diagnostics.
   - Actual: **All checks passed!** (exit 0).
3. Command: `git diff --check`
   - Expected: no whitespace errors.
   - Actual: exit 0; only existing LF-to-CRLF conversion warnings on modified working-copy files.

## Owner authorization clarification — 2026-10-23

- The owner explicitly confirmed VGGT/Hugging Face access approval, directed local download of the VGGT checkpoint, completed authenticated access, and instructed Codex to finish the VGGT work. The owner also clarified that PackLab is non-commercial, should be usable by other people, and its source code should not be exposed or downloadable.
- The pinned `facebook/VGGT-1B-Commercial` checkpoint was downloaded outside Git and its local SHA-256 was verified. **Owner VGGT/Hugging Face access and local-use approval are complete; they are not an open licensing gate.** No repeat owner approval is requested.
- No checkpoint weights have been loaded or executed. The active blockers to local inference are technical: PackLab has no image-asset resolver/output workspace writer or validated VGGT camera-coordinate mapping, and the last recorded free physical RAM was approximately 2.0 GiB for a CPU runtime with a 5 GB checkpoint. Recheck resource headroom before attempting inference.
- Resolved wheel notices and the end-user VGGT AUP/license notice path remain packaging work before distributing a VGGT-enabled PackLab build. This is separate from the owner's completed access/local-use approval; do not report it as a pending owner license acceptance.

## Gates, privacy and publication

- Owner VGGT/Hugging Face access and local checkpoint use are approved and complete; authenticated access, pinned checkpoint download and local SHA verification are recorded above. No checkpoint weights have been loaded or executed. Local inference remains technically blocked on the PackLab image resolver/output writer, camera-coordinate mapping, and sufficient RAM. Resolved-wheel notices and end-user AUP/license notices are required before packaging/distribution; they are not pending owner access/local-use approval. Synthetic test fixtures are not real inference evidence.
- No secrets or credentials were added. Portable provenance omits local paths. No native OCCT/OCP or Installer build was run.
- GitHub Actions/paid CI: none. PR: none. Commit/push: none; no source changes pushed to `main`.
- Worktrees: `NO_LOCAL_WORKTREE_CREATED`.
- Independent review, hosted verification, physical acceptance and release readiness are not claimed.

## Handoff

`LOCAL_ADAPTER_CONTRACT_COMPLETE_OWNER_VGGT_ACCESS_APPROVED_CHECKPOINT_PIN_AND_LOCAL_SHA_VERIFIED_CPU_RUNTIME_PREPARED_REAL_INFERENCE_PENDING_TECHNICAL_INPUT_OUTPUT_COORDINATE_AND_RAM_READINESS` — the VGGT adapter contract and metadata/authority boundary are locally implemented and focused tests pass; the checkpoint revision, size and local SHA-256 are verified; isolated CPU dependencies and the pinned upstream source are present. Owner access/local-use approval is complete. No model weights have been loaded or executed. Real inference is pending a PackLab image-asset resolver/output workspace contract, camera-coordinate validation, and sufficient RAM. Complete bundled runtime notices and the end-user AUP/license notice path are required before distributing a VGGT-enabled build.
