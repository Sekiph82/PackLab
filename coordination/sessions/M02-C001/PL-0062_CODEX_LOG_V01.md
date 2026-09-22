# PL-0062 Codex implementation log V01

Task: PL-0062 — OpenCV marker detection and corner refinement
Prompt: [PL-0062_CODEX_PROMPT_V01.md](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CODEX_PROMPT_V01.md)
Audit criteria: [PL-0062_CHATGPT_AUDIT_CRITERIA_V01.md](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CHATGPT_AUDIT_CRITERIA_V01.md)

## Scope and synchronization

- Live authorization read before work: `TASKS.md` authorized `M02-BATCH-001`,
  `PL-0062` as the next child, and `CODEX` as the required actor.
- Repository: `Sekiph82/PackLab`; branch and push target: `main`.
- Starting commit: `1f80f5f` (`origin/main` matched before implementation).
- Synchronization: `git fetch origin main --prune`, followed by
  `git rev-list --left-right --count HEAD...origin/main` -> `0 0`.
- No destructive Git operation was used. `TASKS.md` was read but not edited.

## Implementation

Published implementation commit: `a2f5b0a7e0874fdbb48c3377a7917e4a95f5f7f4`.

Changed files, all within the PL-0062 allowlist:

- `core/src/packlab_core/calibration/__init__.py`
- `core/src/packlab_core/calibration/marker_detection.py`
- `docs/calibration/marker-detection.md`
- `tests/calibration/test_marker_detection.py`

The PackLab calibration API lazily uses OpenCV's pinned
`DICT_APRILTAG_36h11`, supports the OpenCV detector API variants, applies fixed
`cornerSubPix` refinement, normalizes four corners to clockwise top-left image
pixel order, and returns marker IDs, image-space quality metadata, and
dictionary/policy provenance. Unsupported/malformed images, duplicate IDs,
OpenCV failures, no markers, and unavailable OpenCV are bounded results. The
API has no millimetre, scale, distance, printer, camera-accuracy, or pose
inference.

## Validation evidence

Expected result: the pinned dictionary constant, unsupported shape boundary,
generated positive marker, ordered corners/provenance/no-scale contract, and
duplicate/non-fatal path pass. Failure condition: detector crashes on bounded
invalid input, uses another dictionary, loses corner order, or emits scale.

```text
PYTHONPATH=core/src;temporary OpenCV contrib binding
python -m pytest tests/calibration -q
10 passed in 0.16s
python -m ruff check core/src/packlab_core/calibration tests/calibration
All checks passed!
python -m ruff format --check core/src/packlab_core/calibration tests/calibration
6 files already formatted
```

The positive tests use tiny generated synthetic marker images from temporary
OpenCV 5.0.0 bindings; no private/device image is used. OpenCV runtime and
native/device/physical accuracy evidence are not claimed as owner acceptance.
`git diff --check` and `git diff --cached --check` passed;
`git diff -- TASKS.md` was empty. No private scan, credential, supplier,
signing, or cache artifact was added.

## Publication and handoff

- Implementation pushed to `origin/main` successfully: `1f80f5f..a2f5b0a`.
- Post-push `git rev-list --left-right --count HEAD...origin/main` -> `0 0`.
- This child log is published in a separate commit after the implementation
  commit, as required by the resume batch protocol.

READY_FOR_INDEPENDENT_AUDIT
