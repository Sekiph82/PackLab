# PL-0184 - Codex Remediation Work Order V02

Task: **Remediate immutable segmentation-contract serialization and digest integrity**

Repository: https://github.com/Sekiph82/PackLab  
Cycle: M08-C001 remediation

Source audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0184_CHATGPT_AUDIT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0184_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0184_CODEX_LOG_V02.md

## Authorization gate

Start only when live `TASKS.md` authorizes the M08-C001 remediation batch for
`CODEX`, points to the remediation master prompt/criteria, preserves M07 as
`AUDITED_PASS`, preserves PL-0068 as `OWNER_REQUIRED`, and keeps PL-0186+
and M09 unauthorized. Fetch and compare `origin/main` first; stop on any
tracker, branch, package, or protected-file mismatch.

## Frozen finding and scope

The V01 audit found that `PromptEvidence.data` is assigned a mutable nested
`dict`/`list` structure despite the frozen contract. A caller can mutate the
mapping after construction, changing serialized prompt/provenance content and
making a previously computed `MaskSetRevision.revision_digest` stale. Remediate
only this contract-integrity boundary in
`core/src/packlab_core/segmentation.py` and its dedicated tests:

- recursively freeze JSON-compatible prompt data (or use an equivalent
  fail-closed immutable representation) while preserving deterministic
  `as_dict()` JSON shape;
- prove post-construction mutation of caller-owned and exposed nested values
  cannot change serialized prompt/artifact/revision content or its digest;
- preserve all accepted V01 behavior, source/path/provenance rules, public
  contract names, and the no-model/no-runtime boundary.

Do not modify `TASKS.md`, ChatGPT artifacts, benchmark code, accepted audits,
RAW_CAPTURE bytes, dependencies/locks, model/checkpoint/runtime selection,
private data, or PL-0185+ implementation.

## Validation and handoff

Run focused segmentation tests, the relevant regression subset, the locked full
suite, required Ruff/format/mypy/compileall/diff/protected-file/privacy and
remote checks. Add a sensitive regression test for the frozen nested-data
boundary; record exact commands, expected/failure conditions, results and
limitations in the V02 log. Use separate implementation/evidence and log-only
commits. End the log exactly with `READY_FOR_INDEPENDENT_AUDIT` and stop.
