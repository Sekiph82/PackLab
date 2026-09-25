# PL-0133 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

## Independent finding

The index core is crash-safe and deterministic:
- keyed by capture ID plus whole-package SHA-256;
- same/same registration is idempotent;
- same capture ID/different digest fails with `capture_id_conflict`;
- different capture ID/same digest fails with `digest_identity_ambiguity`;
- atomic temp-file replacement is used;
- restart/reload and concurrent same-identity registration are tested.

Two frozen requirements remain incomplete.

### Conflict result lacks the required digest evidence/quarantine policy

The frozen task requires a stable conflict result containing both non-secret digests and, where appropriate, quarantine handling. `IngestIdentityConflict` currently carries only a string such as `capture_id_conflict`. `ImportService` returns that same string as error code/message and does not include the existing and incoming digests or quarantine the conflicting package.

### No raw-metadata verification/reconstruction path

The index is reloadable from its own JSON file, but there is no verification/rebuild method that cross-checks index records against the immutable raw-store metadata, as required by the reconstructable-or-verifiable criterion.

## Required remediation

Preserve the atomic index. Introduce a structured identity-conflict result containing capture ID plus existing/incoming non-secret digests, define the quarantine/fail-closed path for conflicts, and add index verification/reconstruction from raw-ingest metadata. Test both conflict variants, restart, concurrent attempts, and recovery from a missing/corrupt index using authoritative raw metadata.

PL-0133 remains unchecked.

Decision: **CHANGES_REQUIRED**
