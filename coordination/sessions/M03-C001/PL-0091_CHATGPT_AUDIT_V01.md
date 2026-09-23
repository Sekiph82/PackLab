# PL-0091 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `5bd1ac7959045169e4e8ab291812ff6c85509f8c`

## Independent findings

The child correctly reuses the accepted `PackScanWriter`, whose existing implementation:
- canonicalizes/validates its manifest contract;
- checks declared payload SHA-256 and size;
- creates deterministic ZIP output;
- writes to a temporary partial file and atomically moves it to the destination;
- removes partial output on failure.

That existing writer provides a strong atomic foundation.

The new M03 finalization gate is still incomplete.

### Pre-finalization relationship validation is too shallow

`SessionFinalizer.validate` only verifies:
- the manifest contains at least one `images/` payload;
- `metadata/photos.json` exists in the supplied payload dictionary;
- each declared payload has matching byte count.

It does not validate:
- the authoritative manifest schema before classifying errors;
- per-photo metadata records against the image payloads;
- photo/source IDs/paths/digests using the accepted metadata binding contract;
- the declared SHA-256 values itself at the M03 session-evidence gate.

Some of these checks exist later inside `PackScanWriter`, but the frozen task explicitly requires validating manifest/per-photo/source/checksum relationships before finalization.

### Error classification is not actionable enough

Malformed JSON or an invalid manifest structure falls through the initial guard and becomes `.missingPhoto`, even though `.invalidManifest` exists. `.invalidMetadataBinding` is also declared but never emitted.

### Required positive/negative tests are missing

Criterion 14 / Requirement E requires:
- successful deterministic finalization;
- missing photo;
- bad metadata binding;
- checksum failure.

The child adds only one test with an empty `{}` manifest that expects `.missingPhoto`. It does not exercise the writer, atomic output, success case, bad metadata binding, or checksum failure.

## Criteria

- PASS: 1-10, 12, 16-18
- FAIL: 11, 13, 14, 15, 19-20

## Required remediation

1. Validate the authoritative M02 manifest/photo/source relationships before calling `PackScanWriter`.
2. Distinguish invalid manifest, missing photo, invalid metadata binding and checksum failure with actionable errors.
3. Keep the working session unchanged/resumable on every validation or packaging failure.
4. Add filesystem/contract tests for successful atomic finalization, missing photo, malformed manifest, bad photo/source binding, checksum mismatch and packaging failure/no valid-looking partial destination.
5. Publish a complete task-specific log checkpoint.

PL-0091 remains unchecked.

Decision: **CHANGES_REQUIRED**
