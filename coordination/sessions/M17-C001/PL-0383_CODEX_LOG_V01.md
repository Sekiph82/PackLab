---
coordinationSchema: packlab-coordination/v1
artifactType: codex-log
cycleId: M17-C001
version: 01
actor: CODEX
status: LOCAL_COMPLETE_AUTONOMOUS_QUEUE_ARMED
promptPath: coordination/sessions/M17-C001/PL-0383_CODEX_PROMPT_V01.md
criteriaPath: coordination/sessions/M17-C001/PL-0383_VALIDATION_CRITERIA_V01.md
startingCommit: f8745047063aca6c17378ecb33604e6e1e5b5f02
finalCommit: f8745047063aca6c17378ecb33604e6e1e5b5f02
---

# PL-0383 Codex Log V01 — Engine version diagnostics

## Inputs and synchronization

- Read PL-0383 prompt/criteria, engine capability/version probe source, and `tests/core/test_engine_probe.py`.
- HEAD `f8745047063aca6c17378ecb33604e6e1e5b5f02`; fetched origin `db772e35f386fcba88fa6dbdd01d186959fa7162`; local 0 ahead/95 behind and dirty, no publish/refresh.

## Work and files

- Added a fake executable/version-runner test returning malformed `COLMAP 3.12`. It asserts stable `INVALID` disposition, no parsed version and deterministic diagnostic serialization.
- Existing tests cover missing, invalid, unsupported/wrong, and valid pinned probe versions.
- File: `tests/core/test_engine_probe.py`.

## Validation / limitations

- Expected: fake binary cases report deterministic fail-closed diagnostics without installing/downloading an engine. Relevant test sources exist.
- Full M17 test/Tester suite **NOT RUN**; do not treat test source as a pass. No real engine was invoked by this task.
- No secrets/private data committed. Push/Desktop sync withheld for dirty 95-commit-behind checkout.

**LOCAL_COMPLETE_AUTONOMOUS_QUEUE_ARMED** — missing/wrong/malformed/valid probe coverage is ready for grouped validation; task remains unchecked.
