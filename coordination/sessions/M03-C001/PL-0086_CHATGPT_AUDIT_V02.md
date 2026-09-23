# PL-0086 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `180a719277512e3deee68ec7e8c9dd29b75b9b5e`

## Independent result

The remediation improves fail-closed serialization:
- malformed 4×4 pose shapes are rejected;
- malformed quaternion/rotation-rate shapes are rejected;
- non-finite pose/motion values are rejected;
- record count remains bounded;
- capture IDs receive a basic safe-character transformation.

Two central remediation requirements remain unclosed.

### 1. Explicit units / basis-version contract is still missing

`PoseDiagnosticsExport` currently encodes only:
- `schemaVersion`;
- `timebase = "monotonic_seconds_since_boot"`;
- `coordinateConvention`;
- records.

It still does not encode:
- PackScan `basis_conversion` version;
- translation unit;
- attitude/quaternion order/convention;
- rotation-rate unit.

Thus Windows tooling still cannot interpret all exported sensor fields from explicit versioned units alone.

This directly fails remediation criterion 10.

### 2. Existing diagnostics privacy/redaction boundary is not reused

The exporter performs a local character whitelist on `captureID`.

It does not pass exported string/session context through the existing PackLab diagnostics sanitizer/exporter boundary that already handles secrets, user paths and other sensitive tokens.

A character whitelist is not equivalent to the required shared privacy convention.

### 3. Malformed record validation is still incomplete

The exporter does not reject:
- negative localization epochs;
- empty capture IDs;
- non-finite `PoseSample.timestamp`;
- inconsistent aligned-pose status/sample combinations.

These can still produce misleading diagnostic evidence.

## Criteria

- PASS: 1-9, 11, 15-18
- FAIL: 10, 12, 13, 14, 19

## Required remediation

1. Freeze explicit basis-conversion, translation, attitude/quaternion and rotation-rate units/conventions in the export.
2. Reuse the existing diagnostics privacy sanitizer rather than a one-off capture-ID character transform.
3. Validate malformed IDs/epochs/sample timestamps/status consistency.
4. Add golden tests for the complete Windows-facing contract and shared sanitizer behavior.

PL-0086 remains unchecked.

Decision: **CHANGES_REQUIRED**
