# PL-0184 - ChatGPT Independent Audit V02

## Decision

`CHANGES_REQUIRED`

This V02 decision supersedes the provisional V01 `AUDITED_PASS`. Independent
boundary probing found a material integrity defect in the accepted contract
surface, so PL-0184 remains open and the M08 frontier cannot advance.

## Finding

`PromptEvidence` is a frozen dataclass, but its `data` field is assigned a
mutable recursively nested `dict`/`list` structure by
`core/src/packlab_core/segmentation.py`. Independent probing showed that
mutating `prompt.data` after construction changes `as_dict()` output. Because
`MaskSetRevision` computes its digest from serialized mask artifacts, the same
mutation can change serialized revision content while leaving the stored
`revision_digest` unchanged. This violates the frozen, deterministic,
provenance-bound contract and the digest/revision integrity required by the
PL-0184 criteria.

The defect is reproducible on audited `main` at `04d1ea42a1a7e0977e24e798e9210a9c6d9f6b2d`:

```text
uv run python -c "from packlab_core.segmentation import PromptEvidence, PromptKind; p=PromptEvidence(PromptKind.BOX, {'x':1}); p.data['x']=99; print(p.as_dict()['data']['x'])"
```

prints `99` instead of rejecting or isolating the mutation. The dedicated V01
focused suite passed independently (`8 passed`), but it lacks this mutation-
sensitivity assertion and therefore does not close the finding.

## Criterion dispositions

1. **PASS (E3).** The original batch was authorized and the stopped frontier
   and protected boundaries are verified. The remediation handoff is now
   required before further execution.
2. **FAIL.** Nested prompt data is mutable through the public contract and can
   invalidate serialized revision identity.
3. **FAIL.** No public regression test proves caller/exposed nested-data
   mutation safety or stale-digest rejection; the independent probe proves the
   missing boundary.
4. **PASS (E3).** The audited V01 implementation did not mutate RAW_CAPTURE,
   accepted authority contracts or workspace paths.
5. **PASS (E3).** No model, runtime, dependency, private data, native/physical
   claim or later-child implementation was introduced by PL-0184.
6. **CHANGES_REQUIRED.** The V01 log is structurally complete and ends with
   `READY_FOR_INDEPENDENT_AUDIT`, but the material source defect prevents
   acceptance.

## Required remediation

The bounded V02 prompt and criteria are published at:

- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0184_CODEX_PROMPT_V02.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0184_CHATGPT_AUDIT_CRITERIA_V02.md

The remediation must preserve V01 evidence and must be independently audited
before PL-0185 can be treated as accepted or the batch can proceed.

`CHANGES_REQUIRED`
