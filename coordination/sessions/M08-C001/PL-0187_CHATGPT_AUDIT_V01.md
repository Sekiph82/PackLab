# PL-0187 - ChatGPT Independent Audit V01

Date: 2026-10-01  
Task: **PL-0187 V02 - deterministic mask post-processing**  
Audited implementation: `af79a97ffa1a13a6816ad7e5f1f66fe5f4c8ee40`  
Audited log head: `63c3588c17136952da20cbc39b2e63b0f126a1b0`  
Decision: **CHANGES_REQUIRED**

## Scope reviewed

- Prompt:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CODEX_PROMPT_V02.md
- Criteria:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CHATGPT_AUDIT_CRITERIA_V02.md
- Codex log:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CODEX_LOG_V02.md
- Processor:
  https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/mask_postprocessing.py
- Mask contract:
  https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/segmentation.py
- Tests:
  https://github.com/Sekiph82/PackLab/blob/main/tests/core/test_mask_postprocessing.py
- Accepted predecessor:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_V02.md

## Accepted findings

### Deterministic algorithm and bounded scope - PASS

The pipeline is dependency-free and versioned as `packlab.mask-post-processing/1.0.0`.

The implementation is deterministic and limited to the authorized operations:

- 4-connected enclosed-hole filling;
- 4-connected small-component removal;
- one synchronous conservative single-pixel notch fill;
- no resize, resampling, contour fitting, geometry cleanup, model/runtime changes, hosted service or later-task work.

Operation order is fixed. Edge cleanup reads from a frozen source tuple and applies one bounded pass, so it cannot become iterative smoothing.

### Parameter and threshold semantics - PASS

`MaskPostProcessingParameters` is frozen and deterministic.

The implementation rejects:

- negative thresholds;
- bool-as-int ambiguity;
- non-integer thresholds including non-finite floats;
- thresholds above the project limit;
- thresholds above the parent raster pixel count;
- non-boolean edge-cleanup flags.

Zero disables the area operations. Hole/component thresholds use explicit `<=` semantics.

### Parent immutability and deterministic child identity - PASS

The parent raster values are copied before processing. The child is a distinct `MaskArtifact`. Source image identity, source digest, dimensions and transform semantics are preserved.

The child identity digest includes:

- parent artifact ID;
- parent revision;
- parent digest;
- source identity;
- source dimensions;
- transform;
- pipeline ID/version;
- exact parameters;
- output mask digest.

Creation timestamp is excluded from identity, so repeated processing of the same parent/parameters yields the same artifact/revision/path identity.

### Processing evidence - PASS

The child records processing evidence including:

- parent ancestry;
- exact parameters;
- before/after foreground counts;
- holes/pixels filled;
- components/pixels removed;
- edge notch pixels filled;
- connectivity;
- exact algorithm rules.

`post_processing_evidence` is normalized through the existing JSON freeze boundary.

### Tests and scope - PASS with one missing trust-boundary case

The tests cover deterministic identity, equal-output/different-parameter revisions, parent/source immutability, hole thresholds, component thresholds, 4-connectivity, conservative edge cleanup, empty/full masks, invalid parameters, dimension rejection and predecessor regressions.

The implementation commit changes only:

- `core/src/packlab_core/mask_postprocessing.py`
- `core/src/packlab_core/segmentation.py`
- `tests/core/test_mask_postprocessing.py`

No PL-0188+, M09, dependency/lock, model/checkpoint, private scan or protected lifecycle mutation is present.

Builder evidence records:

- focused suite: `37 passed`;
- full locked suite: `859 passed, 6 skipped, 1 deselected`;
- changed-file Ruff/format/mypy/compile checks passed;
- unrelated repository-wide static debt remains in unchanged files.

## Material finding

### Parent raster bytes are not cryptographically bound to the parent mask digest before processing

`post_process_mask()` accepts `parent.raster` and validates only that its dimensions match `parent.mask_width` and `parent.mask_height`.

It does **not** verify:

```python
parent.raster.digest == parent.mask_digest
```

The current `MaskArtifact` contract also validates the syntax of `mask_digest` and raster dimensions, but does not enforce digest equality when an in-memory raster is present.

PL-0187 then:

1. processes `parent.raster`;
2. uses `parent.mask_digest` as the authoritative parent digest in the child identity and evidence.

Therefore a caller can construct a syntactically valid `MaskArtifact` whose declared digest belongs to different mask bytes, then produce a child whose ancestry claims one parent digest while actually processing another raster.

This breaks the PL-0187 provenance requirement that the unprocessed parent be reproducible and that the child be bound to the actual parent mask revision/digest.

### Required correction

Before any post-processing operation, fail closed unless the in-memory parent raster is cryptographically consistent with the parent artifact:

```python
parent.raster.digest == parent.mask_digest
```

Preferred boundary:

- add the invariant at the general `MaskArtifact` contract when `raster is not None`, because an artifact carrying both a declared digest and raster bytes should never represent inconsistent truth;
- if backward compatibility prevents that, PL-0187 must at minimum enforce the equality inside `post_process_mask()` before reading/processing raster values.

Add regression tests proving:

- matching parent raster/digest is accepted;
- mismatched parent raster/digest is rejected before processing;
- no child/evidence is produced on mismatch;
- existing raw SAM output and legitimate post-processed artifacts remain green.

## Criteria disposition

1. PASS - tracker authorization and predecessor gate were correct.
2. PASS - bounded PackLab-owned operations are implemented.
3. **CHANGES_REQUIRED** - parent object is immutable, but the processor does not prove that the raster being processed is the raster named by `parent.mask_digest`.
4. **CHANGES_REQUIRED** - ancestry fields exist, but parent digest integrity is not enforced.
5. PASS - output identity is deterministic.
6. PASS - parameters are explicit and bounded.
7. PASS - required mask/topology boundary cases are covered.
8. PASS - edge cleanup is conservative and single-pass.
9. PASS - coordinate dimensions/transform semantics are preserved.
10. PASS - SAM-specific runtime/model logic remains outside the processor.
11. PASS - no dependency/hosted/private/later-task expansion.
12. **CHANGES_REQUIRED** - missing public-boundary regression for parent raster/digest mismatch.
13. PASS - added optional evidence field is backward-compatible in serialized shape.
14. PASS as builder evidence for the recorded validation; acceptance remains blocked by the integrity finding.
15. PASS - Codex did not edit lifecycle/owner/audit authority files.
16. PASS - implementation and log commits are separate.
17. PASS - log structure and handoff marker are correct.

## Verdict

`CHANGES_REQUIRED`

PL-0187 remains open. PL-0188+ and M09 remain unauthorized.
