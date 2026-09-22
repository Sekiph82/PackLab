# PL-0059 Codex implementation log V01

Task: PL-0059 — Calibration marker family and IDs
Prompt: [PL-0059_CODEX_PROMPT_V01.md](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0059_CODEX_PROMPT_V01.md)
Audit criteria: [PL-0059_CHATGPT_AUDIT_CRITERIA_V01.md](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0059_CHATGPT_AUDIT_CRITERIA_V01.md)

## Scope and synchronization

- Live authorization read before work: `TASKS.md` authorized `M02-BATCH-001`,
  `PL-0059` as the next child, and `CODEX` as the required actor.
- Repository: `Sekiph82/PackLab`; branch and push target: `main`.
- Starting commit: `4b0e541` (`origin/main` matched before implementation).
- Synchronization: `git fetch origin main --prune`, followed by
  `git rev-list --left-right --count HEAD...origin/main` -> `0 0`.
- No destructive Git operation was used. `TASKS.md` was read but not edited.

## Implementation

Published implementation commit: `2125791a026f85747c4d7172751af4e190798c61`.

Changed files, all within the PL-0059 allowlist:

- `schemas/packscan/calibration-marker-policy.json`
- `docs/calibration/marker-policy.md`
- `tests/calibration/test_marker_policy.py`

PackLab now has one machine-readable marker policy selecting
`DICT_APRILTAG_36h11` via `cv.aruco.getPredefinedDictionary` / the equivalent
C++ constant. It records 6x6 bits, 587 dictionary codes, minimum Hamming
distance 11, dictionary ID bounds `0..586`, active calibration IDs `0..63`,
future PackLab expansion reservation `64..586`, collision rules, and a 40 mm
nominal minimum side guidance explicitly marked `guidance_only` with no
physical accuracy claim. The selected family/dictionary strings are compatible
with the public PackScan marker-observation fields.

The current authoritative capability check used the
[OpenCV 4.13.0 ArUco dictionary reference](https://docs.opencv.org/4.13.0/d1/d21/aruco__dictionary_8hpp.html),
which lists `DICT_APRILTAG_36h11` and `getPredefinedDictionary`. The official
ArUco reference also records the dictionary's code characteristics; these are
not treated as camera, printer, or physical benchmark evidence.

## Validation evidence

Expected result: policy constants, selected family/API names, nominal-unit
guidance, active/reserved boundaries, and dictionary ID boundaries pass.
Failure condition: any drift from the selected dictionary, non-mm guidance,
overlapping/reserved boundary, or malformed policy fails the tests.

```text
python -m pytest tests/calibration/test_marker_policy.py -q
2 passed in 0.04s
python -m ruff check tests/calibration/test_marker_policy.py
All checks passed!
python -m ruff format --check tests/calibration/test_marker_policy.py
1 file already formatted
```

`git diff --check` and `git diff --cached --check` passed;
`git diff -- TASKS.md` was empty. No OpenCV runtime, native/device, printer,
or physical detection/accuracy evidence was fabricated. No private scan,
credential, supplier, signing, or cache artifact was added.

## Publication and handoff

- Implementation pushed to `origin/main` successfully: `4b0e541..2125791`.
- Post-push `git rev-list --left-right --count HEAD...origin/main` -> `0 0`.
- This child log is published in a separate commit after the implementation
  commit, as required by the resume batch protocol.

READY_FOR_INDEPENDENT_AUDIT
