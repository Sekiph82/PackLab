# PL-0076 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `80396298197064d159d57e75e129c83a5e2c5817`

## Independent result

The remediation fixes several major wire-shape defects:
- `not_recorded` and `estimated` statuses exist;
- strict snake_case coding keys are defined;
- orientation is an object;
- ISO wire value is an integer;
- app-only lens/timestamp fields are kept out of the strict photo object;
- source bytes and the metadata document are persisted through a real filesystem path.

The authoritative M02 contract is still not enforced end-to-end.

### 1. Mapper can emit schema-invalid measurement objects

`PackScanPhotoMetadataWire.from` does not enforce the JSON Schema's status constraints.

Examples still possible:
- `status = available` or `estimated` with `source == nil`;
- `status = estimated` with `value == nil`;
- focal length/exposure values <= 0;
- white-balance values outside 1000...100000 K;
- unsupported measurement source strings silently becoming nil.

Those outputs violate `photo-metadata.schema.json` even though Swift encoding succeeds.

### 2. The test does not validate against the authoritative JSON Schema/fixtures

`testPackScanPhotoWireUsesStrictSnakeCaseAndIntegerISO` manually inspects a few encoded keys and types.

It does not run the emitted JSON through the authoritative M02 JSON Schema validator or accepted fixtures as explicitly required by remediation criterion 13.

The child log therefore overstates “cross-contract” closure.

### 3. Accepted source + metadata persistence is not transactionally atomic

`AcceptedPhotoMetadataStore.persist` writes the immutable source first, then rewrites `metadata/photos.json`.

If the metadata write fails after the source succeeds, the source remains on disk without its accepted photo metadata entry. There is no transaction marker/rollback/recovery state distinguishing this orphan from a fully accepted pair.

That does not fully satisfy an atomic accepted-source + metadata binding.

## Criteria

- PASS: 1-9, 11, 15-18
- FAIL: 10, 12, 13, 14, 19

## Required remediation

1. Enforce every schema constraint before encoding, including status/value/unit/source combinations and numeric ranges.
2. Validate emitted Swift JSON against the authoritative M02 JSON Schema/fixtures in automated tests.
3. Make accepted source + metadata commit crash-safe as one logical transaction, with rollback or explicit recoverable transaction state.
4. Add negative schema cases for missing source/value, invalid measurement ranges, invalid source enums and unavailable/not_recorded value leakage.

PL-0076 remains unchecked.

Decision: **CHANGES_REQUIRED**
