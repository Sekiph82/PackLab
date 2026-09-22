# PL-0062 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CHATGPT_AUDIT_CRITERIA_V01.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CODEX_LOG_V01.md

Audited implementation commit: a2f5b0a7e0874fdbb48c3377a7917e4a95f5f7f4

## Blocking findings

### Marker policy is duplicated rather than consumed

PL-0059 created `schemas/packscan/calibration-marker-policy.json` specifically so later detection code cannot silently select a different dictionary.

`marker_detection.py` instead declares its own `DICTIONARY_NAME = "DICT_APRILTAG_36h11"` and directly calls `cv2.aruco.DICT_APRILTAG_36h11`. Neither production code nor the test loads/compares the machine-readable policy source.

If the policy changes, detection and its test can remain green while silently using the old dictionary. The documentation overstates this by saying the detector loads the pinned dictionary from the marker policy.

### Duplicate rejection regression is weak

`test_duplicate_ids_are_flagged_without_crash` accepts `invalid`, `detected`, or `no_markers`. Therefore it does not require duplicate IDs to be flagged when the synthetic duplicate scene is detected.

## Criterion disposition

1-6: PASS
7: **FAIL** — detector does not actually derive the selected dictionary from the PackLab policy source.
8: PASS
9: **FAIL** — duplicate-ID handling is implemented, but the committed regression does not require it.
10: PASS
11: **FAIL** — behavior is not pinned to the machine-readable selected-dictionary source.
12: **FAIL** — tests can stay green across policy drift and duplicate-detection regression.
13-17: PASS
18: **FAIL** — docs/log claim stronger policy integration than the code provides.

Result: **13 / 18 PASS, 5 FAIL**

## Required remediation

Make the PackLab marker policy the canonical source consumed by detection, or generate/import the detector constants from that policy through one shared PackLab module. Add a regression that compares the detector's resolved OpenCV dictionary to the policy file and fails on policy drift.

Strengthen duplicate-ID testing so a controlled duplicate detection result must produce the bounded `duplicate_marker_id` outcome, preferably through injected detector output or a helper-level test rather than accepting multiple unrelated statuses.

Decision: **CHANGES_REQUIRED**
