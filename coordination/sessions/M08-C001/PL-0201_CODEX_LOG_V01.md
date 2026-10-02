# PL-0201 Codex Implementation Log V01

Task: **Suggest targeted recapture sectors**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0201_CODEX_PROMPT_V01.md

Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0201_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Live `TASKS.md` authorized M08 / M08-C001 / the ordered PL-0188 through PL-0201 remaining batch / READY / CODEX. PL-0200 V01 predecessor log was remotely visible at starting main and ended `READY_FOR_INDEPENDENT_AUDIT`.
- Starting synchronized SHA: `a60a35f3aedd9d53a1e86f6915739de86a3a5101`; branch `main`; origin `https://github.com/Sekiph82/PackLab.git`; worktree clean apart from the required PL-0201 log skeleton; local/origin/GitHub-main divergence `0 0`.
- M07 remained `AUDITED_PASS`; PL-0068 remained `OWNER_REQUIRED`; M09/later work remained unauthorized.
- Re-read the live tracker, PL-0201 V01 prompt/criteria, master remaining-batch V02 prompt, coordination README, audit policy, batch protocol, and user-provided repository instructions. No task-state or architecture conflict was found.

## Implementation

Added deterministic, read-only recapture guidance in `core/src/packlab_core/recapture_sector_suggestions.py`.

- Validates the registered-photo ratio contract, observed state, count/ratio consistency, request digest shape, source revision/digest, and denominator against captured camera evidence.
- Reconstructs the PL-0197 coverage policy and report from the supplied captured geometry and requires exact report equality and matching geometry parents before deriving suggestions.
- Computes camera centers from normalized row-major world-to-camera transforms only after finite, affine, and rigid-rotation checks. Uses selected-point centroid directions to classify bounded azimuth/elevation sectors in a normalized world-relative frame.
- Reports inclusive QA threshold gaps for registration, selected-point ratio, mean multiview support, and projected occupancy. QA gaps remain global and are explicitly not attributed to individual view sectors.
- Ranks only unobserved sectors by descending angular gap from observed view directions, then sector ID for deterministic ties. Suggestions include sector indices and angular bounds, global gap context, provenance digests, and no physical-orientation claim.
- Returns `unavailable` without inventing a fallback when evidence is absent or unbound; returns `full_rescan` when observed QA gaps cannot be localized because there is no selected geometry anchor or usable view direction, or when every configured sector is observed while QA gaps remain. Complete QA evidence returns `no_recapture_indicated`.
- Output is bounded by policy (default six suggestions; maximum twelve), carries diagnostic-only authority, and has canonical serialization/SHA-256. It performs no capture/geometry mutation and makes no acceptance or metric-authority claim.

Added `tests/core/test_recapture_sector_suggestions.py` covering partial and complete evidence, empty selected geometry, sector-exhaustion fallback, missing/stale parents, inclusive threshold boundaries, deterministic ordering/serialization, bounded output, physical-frame uncertainty, and source/report immutability.

## Changed files

- `core/src/packlab_core/recapture_sector_suggestions.py`
- `tests/core/test_recapture_sector_suggestions.py`
- `coordination/sessions/M08-C001/PL-0201_CODEX_LOG_V01.md`

## Validation

- Focused: `uv run --locked pytest -q tests/core/test_recapture_sector_suggestions.py` — **5 passed**, exit 0. Initial fixture attempt failed because its synthetic stage-summary contract string did not match the existing sparse-mapping contract; corrected the fixture and reran successfully.
- Predecessor/regression: `uv run --locked pytest -q tests/core/test_recapture_sector_suggestions.py tests/core/test_object_geometry_coverage.py tests/core/test_registered_photo_ratio.py tests/core/test_object_mask_lifting.py tests/core/test_reconstruction_confidence.py tests/core/test_captured_geometry_fit_gate.py` — **45 passed**, exit 0.
- Locked full suite: `uv run --locked pytest -q` — **983 passed, 6 skipped, 1 deselected**, exit 0. Two existing duplicate ZIP-name warnings occurred in `tests/packscan/test_container.py::test_exact_and_casefold_duplicate_names_are_rejected` and `tests/transfer/test_validation_gate.py::test_future_version_checksum_and_unsafe_zip_never_publish_extraction`.
- Changed-file lint: `uv run --locked ruff check core/src/packlab_core/recapture_sector_suggestions.py tests/core/test_recapture_sector_suggestions.py` — passed, exit 0. An initial import-order finding was corrected.
- Changed-file format: `uv run --locked ruff format --check core/src/packlab_core/recapture_sector_suggestions.py tests/core/test_recapture_sector_suggestions.py` — passed, exit 0; initial formatting findings were corrected.
- Targeted types: `uv run --locked mypy core/src/packlab_core/recapture_sector_suggestions.py` — passed, exit 0; an inferred tuple type was made explicit after the initial check.
- Compile: `uv run --locked python -m compileall -q core/src/packlab_core tests/core` — passed, exit 0.
- Whole-repository lint: `uv run --locked ruff check .` — exit 1 for the same two existing findings in untouched `preview/windows/packlab_preview.py` (import sorting and unused `tkinter.ttk`). No changed file was reported.
- Whole-repository format: `uv run --locked ruff format --check .` — exit 1 with 78 existing files that would be reformatted and 1966 already formatted; no unrelated files were formatted or changed.
- `git diff --cached --check` for each implementation commit — passed, exit 0. Staged paths were limited to the two authorized implementation/test files; protected tracker and audit/criteria paths had no staged changes.
- Secret-pattern scan over the implementation, test, and log — no matches, exit 0. `pyproject.toml` and `uv.lock` are unchanged; no dependencies, model/checkpoint downloads, private scans, generated media, binary artifacts, or source capture files were added.
- Public-boundary tests verified geometry, report serialization, and synthetic source bytes remained unchanged after suggestion generation.

## Scope, privacy, and dependency review

- No Studio UI change was needed. No capture actions, source image paths, camera IDs, RAW_CAPTURE bytes, or private material are emitted or modified.
- Sector angles are relative to the selected-point centroid in normalized world XYZ. No gravity, floor, physical up direction, scale, or device-navigation semantics are asserted. Existing aggregate view-support evidence cannot locate a mask gap to a particular camera sector; global QA gaps are carried as context only.
- Native-device, physical capture, owner acceptance, and metric/physical accuracy gates were not run and are not claimed.

## Publication

- Implementation/evidence commits: `d6a179ab8d984d48d8de44d9bcb807b8ee3e4db3` and `73a9c2207ee13089a0fc4efdde89f2a307f64c01`.
- Separate child-log-only commit and final GitHub visibility/parity are recorded in the master log after publication. The log's own commit SHA is indexed there to avoid a self-referential hash inside this file.
- This child does not declare acceptance; it is ready for independent audit.

READY_FOR_INDEPENDENT_AUDIT
