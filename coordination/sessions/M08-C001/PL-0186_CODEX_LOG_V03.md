# PL-0186 — Codex Remediation Log V03

## Handoff

- Task: PL-0186 V03 — runtime and executed-config provenance remediation
- Session: M08-C001
- Starting synchronized SHA: `3e00c6f2e65ac262fde22f5e10decc890e0169eb`
- Implementation SHA: `ca2bfc39254135d56f59011d07f1f06b49b251cf`
- Branch: `main`
- Remote: `origin/main`
- Required actor: CODEX

## Authorization and synchronization

Read before material changes:

- `AGENTS.md`
- `coordination/sessions/M08-C001/PL-0186_CODEX_PROMPT_V03.md`
- `coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_CRITERIA_V03.md`
- `coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_V01.md`
- `docs/architecture/adr/ADR-0004-sam2.1-segmentation-backend.md`
- `docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md`

Commands and results:

- `git fetch origin main --prune` — completed.
- Initial worktree was clean.
- Initial `git rev-list --left-right --count HEAD...origin/main` — `0 4`; local checkout was behind only.
- `git merge --ff-only origin/main` — advanced to `3e00c6f2`.
- Live `TASKS.md` authorized M08-C001 / PL-0186 V03 / CHANGES_REQUIRED / CODEX. It explicitly keeps PL-0187+ and M09 unauthorized.

## Remediation

### Expected and observed SAM 2 identity

The approved identity remains in expected fields only:

- Repository: `https://github.com/facebookresearch/sam2`
- Expected commit: `2b90b9f5ceec907a1c18123530e92e794ad901a4`
- Required source form: a clean Git source checkout of the approved repository/revision.

`SAM21RuntimeIdentity` now separates expected repository/revision from observed SAM 2 availability, package version, source form, module path, source commit, identity match and verification reason. The observation method resolves the imported module path to its Git root, checks the canonical `origin`, reads the actual `HEAD`, and checks the `sam2/` source tree for tracked or untracked changes. It reports an installed package that lacks verifiable source as unavailable for execution. The absolute module path remains in capability diagnostics; `SegmentationProvenance` stores only portable identity fields.

Live environment probe after implementation:

- Python `3.12.10`, native Windows.
- PyTorch and torchvision are unavailable.
- SAM 2 is not importable.
- Observed SAM 2 package version/source form: `unavailable`.
- Observed source revision: `null`.
- Identity match: `false`; reason: `SAM 2 is not importable`.
- Device/CUDA: unavailable.
- Execution capability: unavailable and fail-closed.

Thus the approved revision is not emitted as an observed local runtime fact.

### Executed Hydra config identity

- Removed the arbitrary external `config_path` from `SAM21BasePlusBackend` and `PyTorchSAM21Runtime`.
- The runtime locates `sam2/configs/sam2.1/sam2.1_hiera_b+.yaml` under the verified imported source checkout.
- The config must be present in that source package and match SHA-256 `37d6c56b07a7f8d08baaa314315c60dc3aabe2edc66cd92bac6d1ed50038e788`.
- Digest source: official raw file at `https://raw.githubusercontent.com/facebookresearch/sam2/2b90b9f5ceec907a1c18123530e92e794ad901a4/sam2/configs/sam2.1/sam2.1_hiera_b+.yaml`.
- Predictor construction continues to pass Hydra ID `configs/sam2.1/sam2.1_hiera_b+.yaml` to `build_sam2`, but only after the imported package checkout and the same package's config file pass commit, clean-tree and digest verification.
- Runtime identity and portable provenance record the executed config ID, SHA-256 and verification state. A filesystem lookalike cannot be supplied through the production backend constructor.

Accepted V02 checkpoint identity/hash checks, local-only behavior, lack of network fallback, point/box prompt handling, source-grid masks, failure behavior and source immutability remain covered. PL-0187 post-processing was not changed.

## Changed files

- `core/src/packlab_core/sam21_backend.py`
- `tests/core/test_sam21_backend.py`

No tracker, owner decision, ChatGPT audit/criteria, predecessor evidence, dependency lock, checkpoint binary, private data or later-task file was changed.

## Validation

Focused suites:

- `uv run --locked pytest -q tests/core/test_sam21_backend.py tests/core/test_segmentation.py tests/core/test_segmentation_benchmark.py tests/packscan/test_object_mask_contract.py` — `33 passed`.
- Covered SAM 2 unavailable with null observed revision; approved fake source identity; mismatched and unverifiable source; config digest mismatch; external lookalike rejection; portable provenance; checkpoint hash acceptance/rejection; point/box prompts; malformed output; source-grid metadata; source byte immutability; and no network fallback.

Full locked suite:

- `uv run --locked pytest -q -rs` — `843 passed, 6 skipped, 1 deselected, 2 warnings`.
- Skips: optional `cv2` tests and Windows symlink-privilege tests. Warnings: duplicate ZIP-entry fixture warnings.

Changed-file static checks:

- `uv run --locked ruff check core/src/packlab_core/sam21_backend.py core/src/packlab_core/segmentation.py tests/core/test_sam21_backend.py` — passed.
- `uv run --locked ruff format --check core/src/packlab_core/sam21_backend.py core/src/packlab_core/segmentation.py tests/core/test_sam21_backend.py` — passed.
- `uv run --locked mypy core/src/packlab_core/sam21_backend.py core/src/packlab_core/segmentation.py` — passed.
- `uv run --locked python -m compileall -q core/src/packlab_core/sam21_backend.py tests/core/test_sam21_backend.py` — passed.
- `git diff --check` — passed.

Repository-wide checks:

- `uv run --locked ruff check .` — 2 errors remain in unchanged `preview/windows/packlab_preview.py` (import ordering and unused `tkinter.ttk`).
- `uv run --locked ruff format --check .` — 73 existing unrelated files would be reformatted; all PL-0186 changed files pass.
- `uv run --locked mypy core/src apps/windows-studio/src tools` — 18 errors remain in unchanged `transfer_protocol.py`, `calibration/marker_detection.py`, `packscan/container.py`, `packlab_studio/import_report.py`, and `packlab_studio/receiver.py`.

Scope/privacy/dependency review found only the two intended source/test files changed. `uv.lock` was unchanged; no model binary was added; source scans found no credential or private-data material. No hosted service or download fallback was added.

## Publication

- Implementation commit: `ca2bfc39254135d56f59011d07f1f06b49b251cf` (`Bind SAM 2 runtime and config provenance`).
- Fresh pre-push fetch showed local `main` ahead by one and not behind.
- `git push origin main` — completed from `3e00c6f` to `ca2bfc3`.
- `git ls-remote origin refs/heads/main` — returned `ca2bfc39254135d56f59011d07f1f06b49b251cf`.
- This log is published in a separate log-only commit.

PL-0187+ and M09 were not started. Codex assigns no audit verdict.

READY_FOR_INDEPENDENT_AUDIT
