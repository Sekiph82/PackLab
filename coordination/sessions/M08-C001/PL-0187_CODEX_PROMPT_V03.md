# PL-0187 - Codex Remediation Work Order V03

Task: **Bind post-processing ancestry to the actual parent raster digest**

Repository:
https://github.com/Sekiph82/PackLab

Branch:
`main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Source audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CHATGPT_AUDIT_V01.md

V03 audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CHATGPT_AUDIT_CRITERIA_V03.md

Accepted predecessor:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_V02.md

Required V03 log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CODEX_LOG_V03.md

## Authorization gate

Before material work:

1. `git fetch origin main --prune`
2. inspect `git status --porcelain`
3. inspect `git rev-list --left-right --count HEAD...origin/main`
4. fast-forward only when safe

The live tracker must authorize:

- M08
- M08-C001
- PL-0187 V03
- CHANGES_REQUIRED
- CODEX
- PL-0188+ and M09 unauthorized

Otherwise stop `TASK_STATE_MISMATCH`.

Do not edit `TASKS.md`, owner ADRs, ChatGPT audit/criteria artifacts, accepted predecessor evidence or later-task files.

## Preserve accepted V02 behavior

Keep the accepted PL-0187 implementation intact except for the narrow parent-integrity correction.

Preserve:

- `packlab.mask-post-processing/1.0.0` unless the contract change truly requires a version bump;
- dependency-free implementation;
- 4-connected hole/component semantics;
- exact `<=` thresholds;
- threshold zero disables area operations;
- one synchronous interior-notch fill;
- no image-boundary edge cleanup;
- no resize/resampling;
- deterministic parameter serialization;
- deterministic child identity;
- parent/source immutability;
- processing evidence;
- no PL-0188+ work.

Do not redesign the algorithms.

## Finding to remediate

Today a `MaskArtifact` may carry:

```text
mask_digest = digest A
raster.digest = digest B
```

because the general artifact contract checks raster dimensions but does not verify raster bytes against the declared mask digest.

`post_process_mask()` then processes the raster bytes but writes `parent.mask_digest` into child ancestry and identity.

That allows a child to claim ancestry to digest A while actually being derived from raster B.

This must fail closed.

## Required invariant

Before post-processing consumes parent raster content:

```python
parent.raster.digest == parent.mask_digest
```

must be true.

### Preferred implementation boundary

Prefer strengthening `MaskArtifact.__post_init__`:

```text
if raster is present:
    dimensions must match
    raster.digest must equal mask_digest
```

This makes the domain contract self-consistent everywhere, not only inside PL-0187.

However, preserve backward compatibility for valid artifacts. Existing raw SAM masks and valid post-processed masks must continue to construct and serialize normally.

If repository evidence demonstrates that enforcing this globally would break an accepted legitimate workflow where raster bytes intentionally do not correspond to `mask_digest`, do not invent a workaround. Document the evidence and enforce the equality at the narrow `post_process_mask()` boundary instead.

## Failure behavior

A mismatched parent must fail before:

- hole filling;
- edge cleanup;
- component removal;
- child raster construction;
- child artifact ID/revision calculation;
- child output path calculation;
- post-processing evidence construction/publication.

Raise a PackLab contract/post-processing error with a clear non-secret reason.

Do not silently recompute and replace `parent.mask_digest`.

Do not mutate the parent to repair it.

## Tests

Add regression tests proving:

1. valid parent with matching `mask_digest == raster.digest` is accepted.
2. mismatched declared digest and raster digest is rejected.
3. mismatch yields no child artifact/evidence.
4. raw PL-0186-style artifact with matching digest/raster remains valid.
5. valid post-processed child remains valid under the strengthened contract.
6. repeated valid processing remains deterministic.
7. parent/source immutability remains intact.
8. hole filling threshold regressions remain green.
9. small-component threshold regressions remain green.
10. edge cleanup regressions remain green.
11. PL-0184 and PL-0186 relevant tests remain green.

Use synthetic/public fixtures only.

## Scope

Allowed changes:

- `core/src/packlab_core/segmentation.py` if the generic invariant is adopted;
- `core/src/packlab_core/mask_postprocessing.py` only if needed for the narrow boundary or clearer error translation;
- dedicated PL-0187 tests;
- `coordination/sessions/M08-C001/PL-0187_CODEX_LOG_V03.md`.

Do not add dependencies, model/runtime changes, UI, manual mask correction, invalidation orchestration, geometry work or later-task code.

## Validation

Run:

- PL-0187 focused tests;
- relevant PL-0184/PL-0186 regressions;
- exact locked full pytest suite;
- Ruff;
- format check;
- targeted/relevant mypy;
- compileall;
- `git diff --check`;
- protected-file/scope review;
- dependency/license review;
- privacy/secrets/signing review;
- generated/binary review;
- remote visibility/freshness checks.

Report unrelated pre-existing repository debt truthfully without changing unrelated files.

## Publication

Create separate commits:

1. implementation/evidence commit(s);
2. log-only commit:
   https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CODEX_LOG_V03.md

The log must include:

- synchronized starting SHA;
- implementation SHA(s);
- exact invariant location;
- mismatch failure behavior;
- tests;
- full/static validation;
- changed files;
- residual limitations;
- confirmation that PL-0188+ and M09 were not started.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Stop. Independent ChatGPT audit is required before PL-0188.
