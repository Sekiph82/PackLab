# PL-0072 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `882d386500f5412f546a0fdfac0b9d6d6338e778`

## Independent result

The remediation successfully adds real immutable source persistence:
- exact source bytes are written atomically;
- digest/dimensions are validated before write;
- conflicting source content is rejected;
- the source record can be reopened;
- same-content persistence is idempotent.

The previous audit is not fully closed.

### 1. HEIF/JPEG metadata extraction/preservation is still absent

Final `main` contains no ImageIO / `CGImageSource` metadata extraction path.

`OriginalSourceRecord.metadataBytes` remains a caller-supplied `Data` field. The store simply encodes whatever metadata bytes were supplied; it does not derive EXIF/TIFF/HEIF/JPEG metadata from the captured source payload and cannot prove unknown metadata preservation.

This directly fails remediation criterion 11.

### 2. Required metadata/derivative/dimension tests are incomplete

The added filesystem test covers:
- successful source write;
- record reopen;
- idempotent same-content write;
- digest mismatch.

It does not cover:
- metadata extraction/preservation from an encoded image;
- unknown metadata retention;
- physical derivative-path separation/overwrite protection;
- dimension mismatch.

Thus remediation criteria 13-14 are not fully satisfied.

### 3. Existing-source idempotency does not validate the sidecar record

When the source file already exists with the expected digest, `persist` returns the source URL immediately. It does not verify that the corresponding `captureID.source.json` record exists and matches. A missing/corrupt sidecar can therefore be treated as a successful idempotent persistence.

## Criteria

- PASS: 1-10, 12, 15-18
- FAIL: 11, 13, 14, 19

## Required remediation

1. Extract available source metadata directly from the captured HEIF/JPEG bytes with ImageIO and preserve it in the immutable source record.
2. Validate the sidecar record on idempotent reopen, and repair/fail closed rather than returning success with a missing/corrupt record.
3. Add behavior-bearing tests for metadata extraction/round-trip, unknown metadata preservation where possible, dimension mismatch, derivative separation and sidecar corruption.

PL-0072 remains unchecked.

Decision: **CHANGES_REQUIRED**
