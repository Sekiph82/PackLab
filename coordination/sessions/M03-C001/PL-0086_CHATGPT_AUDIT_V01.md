# PL-0086 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `3120bc3cc58416ef2dd38249437435e3be1a2f0a`

## Independent findings

The child adds useful export foundations:
- deterministic sorted JSON;
- explicit export schema version;
- a declared monotonic timebase;
- coordinate convention;
- capture/pose/motion/epoch records;
- record-count cap;
- rejection of some non-finite pose/timestamp data;
- no Windows ingest pulled forward.

Mandatory export-contract protections are still incomplete.

### Units/frame contract is incomplete

The export declares a timebase and coordinate convention, but does not explicitly encode the relevant translation/rotation-rate/attitude units or a distinct coordinate-frame/basis-conversion version required for reliable Windows interpretation.

### Malformed data validation is incomplete

The exporter checks pose-transform finiteness but not:
- transform length/4×4 validity;
- motion attitude length/finiteness;
- rotation-rate length/finiteness;
- negative/invalid epoch or malformed capture identity.

A finite malformed transform can therefore be serialized as valid-looking diagnostics.

### Privacy convention is not actually applied

The frozen requirement calls for reuse of existing diagnostics privacy/redaction conventions. The export directly encodes its records and does not pass relevant free-form/session references through the established diagnostics sanitizer. The current model happens to expose few string fields, but the required privacy boundary is not implemented.

### Required bounded/golden tests are incomplete

The inspected test checks one successful encoding and one infinite timestamp. It does not exercise the `tooManyRecords` boundary despite the log claiming bounded-export tests, and does not golden-check units/timebase/frame semantics.

## Criteria

- PASS: 1-9, 17-18
- FAIL: 10, 11, 12, 13, 14, 15, 16, 19-20

## Required remediation

1. Freeze explicit units, timebase and coordinate/basis version fields suitable for Windows analysis and align them with accepted PackScan contracts.
2. Fail closed on wrong-size/non-finite pose and motion arrays and other malformed record fields.
3. Reuse the existing diagnostics privacy/redaction boundary for any exported string/session context.
4. Add deterministic golden serialization plus exact maximum-record/over-limit, malformed transform, malformed motion and redaction tests.
5. Publish a complete task-specific log checkpoint.

PL-0086 remains unchecked.

Decision: **CHANGES_REQUIRED**
