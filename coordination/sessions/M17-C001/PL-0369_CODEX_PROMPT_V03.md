# PL-0369 — Codex Prompt V03

Task: **Create small synthetic CI golden dataset with owner-authorized internal-use terms**  
Milestone: **M17 — Validation, Benchmarking & Reliability**  
Cycle: **M17-C001**

V03 supersedes V02's M17-S01 test checkpoint timing after the owner's instruction that testers and grouped tests run at the end of the milestone. V02 and V01 remain historical records. The owner decision is preserved in `PL-0369_OWNER_DECISION_INTERNAL_USE_V01.md`.

## Authority and scope

- Root `TASKS.md` authorizes PL-0369 and remains the only live tracker.
- Use the existing six hash-pinned synthetic media fixtures and five PackScan corpus cases; do not copy or modify payloads.
- The owner authorized a dataset-scoped internal-use license for PackLab development/CI and owner-controlled design-office and Kenya-factory use. This does not grant third-party reuse, sublicensing, external redistribution, or sale/marketing rights, does not license the whole repository, and does not assert formal legal review.
- Keep private Kenya data, credentials, physical ground truth, reconstruction accuracy and manufacturing claims out of this dataset.
- No new media allowlist or workflow change.

## Validation schedule

- Inspect and obtain independent source and security/licensing reviews of the actual implementation and terms.
- Do not run tests, Tester, Ruff, or mypy per task or at an M17 sprint boundary. Defer the grouped M17 validation to the milestone-end checkpoint after M17 tasks PL-0369–PL-0395 have been implemented or their genuine external blockers documented.
- Keep PL-0369 unchecked until that grouped validation passes. A source review is not test evidence or formal legal approval.

