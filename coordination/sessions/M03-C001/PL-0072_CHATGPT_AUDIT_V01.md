# PL-0072 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `b553b733ed6fbf53af9f2622beb55f7fbd3e9ae6`

## Independent finding

The child adds useful integrity primitives:
- SHA-256 digesting;
- source dimensions/orientation fields;
- a separate derivative path;
- fail-closed digest/dimension checks;
- deterministic positive/negative integrity tests.

However the frozen task requires actual preservation of captured source metadata, not only a record type.

### Missing source persistence/extraction

The inspected implementation does not persist original still bytes anywhere. `OriginalSourceRecord` stores metadata about a source and a digest, but no write path or immutable source-store operation is added in this child.

It also does not extract/preserve EXIF/TIFF/HEIF/JPEG metadata from captured image bytes. `metadataBytes` is simply an injected `Data` field. There is no ImageIO/CGImageSource metadata extraction, no preservation of unknown metadata, and no proof that source metadata is carried from the actual capture artifact.

Consequently:
- criterion 10 / Requirement A is incomplete;
- criterion 11 / Requirement B is not implemented;
- criterion 14 / Requirement E does not prove derivative logic cannot overwrite a real stored master, only that a generated derivative path differs.

## Criteria

- PASS: 1-9, 12-13, 16-18
- FAIL: 10, 11, 14, 15, 19-20

Criterion 19 is also incomplete because the child log does not record a task-specific log commit checkpoint as required by the frozen criteria.

## Required remediation

1. Add an immutable original-source persistence path that writes the exact capture bytes and verifies the resulting digest/dimensions.
2. Extract available image metadata from the original HEIF/JPEG payload using an appropriate Apple metadata API and preserve unknown metadata where technically safe.
3. Keep preview/thumbnail generation physically separate from the master source path and prove it cannot overwrite the master.
4. Add behavior-bearing tests for metadata extraction/preservation, immutable write protection, digest mismatch and dimension mismatch.
5. Publish a complete task-specific child log checkpoint.

PL-0072 remains unchecked.

Decision: **CHANGES_REQUIRED**
