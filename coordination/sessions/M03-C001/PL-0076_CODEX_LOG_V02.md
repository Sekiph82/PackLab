# PL-0076 — Codex Remediation Log V02

- Authorization: M03-BATCH-002 / READY / CODEX; PL-0070 accepted; PL-0068 OWNER_REQUIRED; no M04 work.
- Prompt/criteria/prior audit read: PL-0076 V02/V02/V01.
- Implementation commit: `8039629` (`fix(PL-0076): align photo metadata with PackScan schema`).

The strict `PackScanPhotoMetadataWire` and `PackScanPhotoMetadataDocument` models now encode `schema_version`, snake_case fields, source statuses including `not_recorded` and `estimated`, orientation objects, optional status-constrained measurements, and integer ISO values. Lens identity and capture timestamp remain in `PhotoCaptureAppMetadata` and are excluded from the strict photo object. `AcceptedPhotoMetadataStore` validates the source binding and atomically replaces the metadata document after immutable source persistence. Tests cover wire keys, ISO type, unavailable/estimated fields, mismatch rejection, duplicate IDs, and reopenable filesystem output.

Validation:

- `git diff --check`: passed.
- `$env:PYTHONPATH=(Join-Path (Get-Location) 'core/src'); python -m pytest -q`: `162 passed, 4 skipped, 1 deselected, 1 warning`.
- Native Xcode/iPhone execution is unavailable on this Windows workspace and is not claimed.
- No TASKS/audit edits, secrets, private assets, caches, or signing material.

Prior findings addressed: schema mismatch, wrong status/ISO/orientation encoding, app-only field leakage, validation-only persistence, and missing cross-contract behavior tests.

READY_FOR_INDEPENDENT_AUDIT
