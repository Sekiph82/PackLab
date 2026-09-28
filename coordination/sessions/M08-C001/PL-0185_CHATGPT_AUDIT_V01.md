# PL-0185 - ChatGPT Independent Audit V01

## Decision

`CHANGES_REQUIRED`

PL-0185 is not independently accepted. The deterministic benchmark and the
explicit no-selection license/checkpoint blocker are truthful, but the public
report contract has a material digest-integrity defect. The batch remains
stopped and PL-0186+ are not accepted or authorized by this audit.

## Audit scope and evidence

- Repository: https://github.com/Sekiph82/PackLab
- Audited head before this audit: `c4922b8bf956cafb0b79e26950ff3c2097578d97`
- Frozen prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0185_CODEX_PROMPT_V01.md
- Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0185_CHATGPT_AUDIT_CRITERIA_V01.md
- Implementation commit: `63ddbb249dc6fdd5f4875e38b613939d03731d17`
- Child-log commit: `f00d1a97393f2989f979e3e7b6fca5996df44aa1`
- Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0185_CODEX_LOG_V01.md
- Benchmark report: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/evidence/M08-PL-0185-segmentation-benchmark-v01.md

The checkout was verified on `main` with `origin/main` equal to the local head
and a clean worktree. The original implementation range added only the
benchmark module, dedicated tests and bounded report; its separate log commit
contains only the child log.

## Criterion dispositions

1. **PASS (E3).** The original live tracker authorized the complete M08-C001
   batch and PL-0185 frontier, with PL-0184 evidence remotely visible and M07,
   PL-0068 and M09 boundaries preserved.
2. **PASS (E3, subject to the finding below).** The actual implementation is a
   PackLab-owned, dependency-free deterministic harness with five required
   public-safe synthetic classes, explicit baseline candidates, quality
   metrics, provenance/runtime/license/checkpoint fields, failure modes,
   thresholds, reproducible report digest and an explicit
   `NO_SELECTION_LICENSE_OR_CHECKPOINT_BLOCKER`. It does not install/select a
   production model or claim synthetic overlap as physical accuracy.
3. **FAIL.** `BenchmarkCase.__post_init__` converts `predictions` to a plain
   mutable `dict` even though the dataclass is frozen. Independent probing on
   the audited source successfully replaced a prediction after report
   construction; `report.as_dict()` then changed while the stored
   `report_digest` remained unchanged. This violates reproducible report
   digest integrity and is not covered by the V01 tests.
4. **PASS (E3).** The actual PL-0185 implementation range does not modify
   RAW_CAPTURE/source bytes or predecessor authority contracts. The dedicated
   sentinel test and source inspection agree with that boundary.
5. **PASS (E3).** No unreviewed dependency/model/runtime, private data,
   generated reconstruction output, UI-owned truth, native/physical claim or
   later-child implementation was introduced. The no-selection blocker is
   correctly retained rather than bypassed.
6. **CHANGES_REQUIRED.** The child log records the required checks and ends
   exactly with `READY_FOR_INDEPENDENT_AUDIT`, but the material mutable report
   boundary prevents acceptance.

## Independent checks

- `uv run --locked pytest -q tests/core/test_segmentation_benchmark.py tests/core/test_segmentation.py`
  -> `15 passed`, exit `0`.
- Independent mutation probe against the committed public API demonstrated
  `MUTABLE_PREDICTIONS True` and `DIGEST_STALE True`.

The green suite is insufficient because it does not attempt mutation of the
nested report mapping. The separate model/license/checkpoint blocker remains a
truthful prerequisite for PL-0186 after this integrity remediation.

## Required remediation

- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0185_CODEX_PROMPT_V02.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0185_CHATGPT_AUDIT_CRITERIA_V02.md

The remediation must preserve the V01 benchmark evidence and may not treat
this audit as permission to start PL-0186.

`CHANGES_REQUIRED`
