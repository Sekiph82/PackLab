# PL-0374 — Codex Prompt V01

Task: **Add a regression harness for metric-band comparisons**  
Milestone: **M17 — Validation, Benchmarking & Reliability**  
Cycle: **M17-C001**

## Scope

- Provide a reusable benchmark comparison boundary that compares observed engine metrics to exact expected sample ranges.
- Use inclusive bounds; classify each metric and aggregate outcome deterministically.
- Reject missing/extra keys, booleans, strings, NaN, infinities, malformed bands and real/authority-ambiguous synthetic fixture records.
- Preserve provenance, unit and measurement authority in the result. Synthetic outputs remain software-only evidence.
- Keep the small CI test fixtures synthetic/programmatically generated; do not add licensed YCB photos/models or private data to Git.

## Validation timing

- Add positive, boundary, negative and provenance regression cases to the M17 batch. Do not run the tester or comprehensive suite after this child task.
- Run grouped M17 tests and consolidated code/security reviews at milestone end.
- Write `PL-0374_CODEX_LOG_V01.md` with implementation evidence, test deferral and limits.
