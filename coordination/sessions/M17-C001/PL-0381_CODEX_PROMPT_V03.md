# PL-0381 — Codex Prompt V03

Task: **Fail-closed disk-space-provider failures and malformed results**  
Milestone: **M17** · Cycle: **M17-C001**

V03 closes the PL-0381 V02 independent-review gap. V02 already injects zero free space and authority-publish `ENOSPC`, but lacks direct tests for a provider that raises and for malformed returned values.

## Scope

- Translate ordinary provider exceptions into actionable `ProjectError` before authority publication.
- Add disposable-project regression cases for `OSError`, another ordinary exception, and malformed values including bool, negative integer, float, and `None`.
- Assert authority bytes, editable-state bytes, revision, immutable raw bytes, and temp files remain unchanged in every failure case.
- Do not fill real disks, alter owner projects, or add cleanup behavior.

## Test timing

- Do not run tests for this child. The owner directed grouped milestone-end testing, and M17's two broad runs have already occurred. New test sources remain unexecuted until the next expressly authorized consolidated validation.
- Write `PL-0381_CODEX_LOG_V03.md` after independent source review; do not claim V03 test acceptance.
