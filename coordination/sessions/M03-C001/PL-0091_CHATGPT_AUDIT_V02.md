# PL-0091 — ChatGPT Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `a8d5fff92f486873eaa5fc8e1f4c4aa3fa36ce3d`
Remediation log: `PL-0091_CODEX_LOG_V02.md`

## Independent result

The remediation improves the preflight substantially:
- malformed manifest is distinguished from missing-photo errors;
- metadata is decoded through the strict Swift PackScan wire model;
- photo/image filename binding is checked;
- declared sizes and SHA-256 digests are checked before `PackScanWriter`.

The frozen remediation is still incomplete.

### Authoritative manifest contract is only partially prevalidated

The preflight checks schema version, checksum algorithm and payload records, but does not fully enforce the M02 manifest contract before invoking the writer, including canonicalization value, safe/unique payload set semantics and all required manifest relationships.

### Required successful atomic finalization evidence is missing

The remediation criteria explicitly require filesystem/contract tests for:
- successful atomic finalization;
- malformed/missing data;
- bad binding;
- checksum mismatch;
- no valid-looking partial destination on packaging failure.

The added tests cover malformed manifest, empty metadata and checksum mismatch. They do **not** execute a successful `SessionFinalizer.finalize` path and do not verify output existence/content, destination collision/failure behavior, or absence of partial output after packaging failure.

### Resumability on failure is asserted but not demonstrated

Because tests call `validate` rather than the actual `finalize` failure path, they do not prove the working session remains untouched/resumable when writer/finalization fails.

## Required remediation

1. Prevalidate every M02 manifest/photo/source/checksum relationship required for this M03 gate, including checksum canonicalization and safe payload-set semantics.
2. Add a real successful `SessionFinalizer.finalize` filesystem test.
3. Add packaging/destination failure tests proving no valid-looking partial .packscan remains.
4. Prove the source working session remains unchanged after validation/writer failure.
5. Preserve distinct actionable error classes.

PL-0091 remains unchecked.

Decision: **CHANGES_REQUIRED**
