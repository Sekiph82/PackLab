# PL-0373 — Codex Prompt V01

Task: **Store parametric-fit metric expectations with tolerance bands**  
Milestone: **M17 — Validation, Benchmarking & Reliability**  
Cycle: **M17-C001**

## Scope

- Store expected parametric-fit extents per axis alongside the synthetic sample's generated PLY geometry and declared scenario tolerance.
- Preserve metric names, units, provenance and `NONPHYSICAL_SOFTWARE_TEST_ONLY` authority in every record.
- Ensure the comparison API accepts only explicitly synthetic samples with complete, well-formed metric bands.
- Do not claim editable Design Model fit, moldability, supplier tolerance or physical fit from generated ground truth.

## Validation timing

- Add boundary/negative cases to the M17 grouped test batch; do not run pytest/tester after this task.
- Run full M17 tests and consolidated reviews at milestone end. A bounded dataset artifact integrity check may run after generation.
- Write `PL-0373_CODEX_LOG_V01.md` with implementation evidence and all outstanding limits.
