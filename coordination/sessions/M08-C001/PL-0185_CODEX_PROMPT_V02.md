# PL-0185 - Codex Remediation Work Order V02

Task: **Remediate benchmark report immutability and digest integrity**

Repository: https://github.com/Sekiph82/PackLab  
Cycle: M08-C001 remediation

Source audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0185_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0185_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0185_CODEX_LOG_V02.md

## Authorization gate

Start only after PL-0184 V02 has independently passed and the live tracker
authorizes this M08-C001 remediation child in order. Fetch and compare
`origin/main` first; stop on tracker, branch, package, predecessor-log or
protected-file mismatch. PL-0186+ and M09 remain unauthorized.

## Frozen finding and scope

The V01 audit found that `BenchmarkCase.predictions` is a mutable plain
`dict` inside a frozen dataclass. A caller can mutate a report after its
`report_digest` is computed, changing serialized case content while retaining
the old digest. Remediate only this benchmark-contract integrity boundary in
`core/src/packlab_core/segmentation_benchmark.py` and its dedicated tests:

- make nested prediction state immutable or equivalently mutation-safe while
  preserving deterministic `as_dict()` output and the public benchmark shape;
- prove post-construction mutation cannot change report content/digest or
  silently replace a prediction;
- preserve the five synthetic classes, metrics, provenance/license/checkpoint
  blocker and no-selection decision exactly.

Do not modify `TASKS.md`, ChatGPT artifacts, accepted audits, segmentation
contract code, dependencies/locks, model/checkpoint/runtime selection, private
data, RAW_CAPTURE bytes, or PL-0186+ implementation.

## Validation and handoff

Run focused benchmark plus predecessor tests, the locked full suite, required
Ruff/format/mypy/compileall/diff/protected-file/privacy and remote checks. Add a
mutation-sensitive regression test; record exact commands and results in the
V02 log. Use separate implementation/evidence and log-only commits. End the
log exactly with `READY_FOR_INDEPENDENT_AUDIT` and stop.
