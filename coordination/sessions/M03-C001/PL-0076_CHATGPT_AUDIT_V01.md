# PL-0076 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `20fe7e902ba9945c68361625669384c938e0e362`

## Independent findings

The child adds useful binding primitives:
- per-photo capture identifiers/path/sequence/dimensions/lens fields;
- explicit measurement status/value/unit/source structure;
- source-image digest/dimension/ID/path validation;
- deterministic mismatch tests.

However the frozen criteria require **PackScan-contract alignment and persistence for every accepted still**. The inspected model is materially incompatible with the accepted M02 JSON Schema.

### M02 schema mismatch

Authoritative schema:
`schemas/packscan/photo-metadata.schema.json`

Observed incompatibilities include:

1. Schema source status values are:
   - `available`
   - `unavailable`
   - `not_recorded`
   - `estimated`

   Swift `SourceValueStatus` defines `available`, `unavailable`, `notRecorded`.
   It therefore encodes the wrong wire value for `not_recorded` and omits `estimated`.

2. Schema ISO value is an **integer**. `SourceMeasurement.value` is always `Double?`.

3. Schema orientation is an object with `value`, optional `rotation_degrees`, and `source`. Swift uses a plain `String`.

4. The schema photo object has `additionalProperties: false`. `PhotoCaptureMetadata` introduces fields such as `lensIdentity` and `captureTimestamp` that are not part of that photo object contract.

5. Field naming/wire structure is Swift-camelCase and is not demonstrated to encode into the schema's required snake_case names/objects.

No test serializes `PhotoCaptureMetadata` and validates it against the accepted JSON Schema.

### Persistence/atomicity is not implemented

The child creates a model and validation helper, but no persistence operation atomically writes the per-photo metadata alongside the immutable source record. Therefore criterion 10 and criterion 12 are incomplete.

## Criteria

- PASS: 1-9, 13, 16-18
- FAIL: 10, 11, 12, 14, 15, 19-20

## Required remediation

1. Make the Swift wire model encode exactly to the accepted M02 `photo-metadata.schema.json`, including status strings, orientation structure, measurement types/units/sources, required fields and allowed properties.
2. Keep any app-only lens/timestamp state in a separate internal model or map it into the correct accepted PackScan contract location.
3. Add a real atomic persistence/binding path for accepted source + metadata.
4. Add cross-contract tests that encode Swift metadata JSON and validate it against the authoritative M02 schema/fixtures, including unavailable/estimated and mismatch cases.
5. Publish a complete task-specific log checkpoint.

PL-0076 remains unchecked.

Decision: **CHANGES_REQUIRED**
