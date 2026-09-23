# PL-0088 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `d60c1526cb1b9aa02438a0688be8c093c61d95eb`

## Independent findings

The child adds meaningful storage primitives:
- per-session root;
- metadata/state/images/previews/tmp separation;
- duplicate session/source rejection;
- atomic replacement for metadata/state;
- immutable-by-name source storage;
- temporary-file cleanup on the immediate atomic-write error path.

Mandatory storage contract and validation remain incomplete.

### Per-photo record layout is missing

Requirement A explicitly includes metadata, immutable source photos, **per-photo records**, and transient state. The layout defines no dedicated per-photo metadata/record location.

### Incremental persistence is not integrated with accepted capture flow

`writeState(Data)` and `storeSource(Data,named:)` are generic APIs. No implementation atomically/incrementally writes the accepted still plus its per-photo record and advances session state after an actual accepted capture. Requirement C is not demonstrated.

### Stale-temp/reopen recovery rules are missing

The store removes only the temporary file created by the currently failing `atomicWrite`. There is no startup/reopen scan for stale temp files, interrupted partial state, or recovery validation. Requirement D is incomplete.

### Frozen failure-injection tests were not added

Requirement E explicitly requires tests for:
- interrupted writes;
- stale temp files;
- duplicate IDs;
- reopen validation.

The inspected child adds only `testSessionStorageLayoutSeparatesSourcesDerivativesAndTemps`. No filesystem failure-injection behavior is exercised. The Codex log claim that persistence seams were covered is therefore overstated.

## Criteria

- PASS: 1-9, 11, 16-18
- FAIL: 10, 12, 13, 14, 15, 19-20

## Required remediation

1. Add a canonical per-photo-record layout and schema-compatible record persistence.
2. Create one accepted-capture persistence transaction/workflow that writes immutable source + per-photo record + incremental session state safely.
3. Add reopen validation and stale-temp recovery/cleanup semantics.
4. Add real temporary-directory/failure-injection tests for interrupted write, stale temp, duplicate session/source IDs, successful reopen and corrupt/incomplete reopen.
5. Preserve immutable raw source semantics and publish a complete task-specific log checkpoint.

PL-0088 remains unchecked.

Decision: **CHANGES_REQUIRED**
