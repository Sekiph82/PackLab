# PL-0130 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

## Independent finding

The quarantine implementation itself is well structured:
- quarantine is outside normal raw/import directories;
- package bytes are preserved under a SHA-256-derived collision-safe filename;
- structured event history is atomically updated;
- package-provided filenames are not reused as quarantine destinations;
- capture_id is read only when safely parseable;
- diagnostics are reduced to stable error codes and private absolute paths are not persisted;
- repeated quarantine of the same bytes reuses one package and appends event history.

However, the frozen V01 test matrix is not fully satisfied.

### Required quarantine cases are not actually tested

The PL-0130 test named `test_future_and_unsafe_packages_are_quarantined_without_normal_artifacts` writes plain `b"future bytes"` to a file. That exercises corrupt ZIP handling, not a genuine future-schema PackScan.

There is no dedicated PL-0130 test proving quarantine behavior for:
- a valid ZIP with unsupported future schema;
- an internal PackScan checksum mismatch;
- a malicious source/package filename/path attempting to influence quarantine destination.

The later M05 integration tests cover some invalid categories, but they do not close the specific checksum-mismatch quarantine case required here.

## Required remediation

Preserve `QuarantineStore`. Add real package fixtures/tests for future schema, manifest/internal checksum mismatch, malicious filename/path, corrupt ZIP, repeated quarantine, and explicit proof that none of those inputs creates normal raw/import artifacts.

PL-0130 remains unchecked.

Decision: **CHANGES_REQUIRED**
