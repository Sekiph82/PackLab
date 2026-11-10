# PL-0372 — Codex Prompt V01

Task: **Store reconstruction metric expectations with tolerance bands**  
Milestone: **M17 — Validation, Benchmarking & Reliability**  
Cycle: **M17-C001**

## Scope

- Attach per-sample reconstruction metric ranges to the M17 synthetic benchmark using persisted generated geometry as the dimensional reference.
- Label each range with units, scenario provenance and nonphysical software-test authority. Segmentation overlap thresholds may use existing PackLab synthetic benchmark policy; do not present them as physical accuracy limits.
- Reject absent, malformed, reversed, nonfinite, extra or authority-ambiguous ranges in the data validator.
- Keep real YCB and future Kenya physical dimensions distinct; no synthetic range can close physical reconstruction acceptance.

## Validation timing

- Add regression coverage to the M17 grouped test batch. Do not run pytest/tester per task; run the full consolidated M17 validation at milestone end.
- Dataset artifact validation may run after generation as a bounded integrity check, distinct from the M17 software test suite.
- Write `PL-0372_CODEX_LOG_V01.md` with exact implementation, evidence and limitations.
