# PL-0109 — ChatGPT Remediation Audit V03

Decision: **CHANGES_REQUIRED**

## Independent result

The remediation adds the requested mixed required-detail test and proves that a persisted `CompletionDiagnostics` snapshot can be loaded into a newly configured runtime.

However, the frozen V03 requirement is not fully satisfied because the **underlying detail-pass state is still not persisted/restored**.

### Concrete resume defect

`M04ScanContext` persists:
- preset;
- base pass;
- completion snapshot;
- quality guidance;
- asymmetric coverage;
- turntable coverage;

but it does **not** persist detail-pass coverage/evaluations.

On resume, the app calls `restoreCompletion()`, which only assigns the saved completion snapshot. The fresh runtime's `m04DetailEvaluations` and detail coverage models remain empty.

Any subsequent accepted capture or other event that calls `recomputeM04Completion()` rebuilds completion from the fresh runtime's empty detail-pass state, so previously completed detail passes can be lost and previously persisted completion becomes non-reproducible.

The new test currently verifies only:

`persisted completion -> restoreCompletion -> same completion value`

It does not prove:

`persisted pass evidence -> fresh runtime reconstruction -> recomputed same completion`.

That is the behavior explicitly required by the V03 remediation.

## Required remediation

Persist the minimum authoritative detail-pass state needed to reconstruct completion after resume. Prefer persisted accepted detail-pass coverage/evaluations or deterministic reconstruction from canonical accepted capture records.

Then add a fresh-runtime resume test that:
1. persists mixed required detail-pass evidence;
2. creates a new runtime;
3. restores/reconstructs the detail-pass state;
4. recomputes completion;
5. proves the same completed/missing passes and score;
6. performs one additional accepted capture after resume and proves prior detail completion is not lost.

Do not merely restore a precomputed completion snapshot as the sole source of truth.

PL-0109 remains unchecked.

Decision: **CHANGES_REQUIRED**
