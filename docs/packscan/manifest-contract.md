# PackScan manifest contract 1.0

`manifest.json` is the package index and is validated against
`schemas/packscan/manifest.schema.json`. It is intentionally strict:
unknown properties are rejected, timestamps must be UTC ISO-8601 values with a
`Z` suffix, and all payload paths are relative normalized ZIP paths.

The manifest identifies the capture with a stable `capture_id`, records the
iOS device summary and versioned capture mode, and declares every package file
with its role, authority, byte length, media type where applicable, and
lowercase SHA-256 digest. `source_evidence.immutable` is always `true`;
previews, masks, thumbnails, and diagnostics are `derived` and cannot replace
source images or measurement truth.

`schema_version` is the schema contract version and is not inferred from a
filename. A future major/minor structure is rejected until an explicit schema
revision declares compatibility. A local time such as `2026-09-22 12:00:00`
is invalid because it has no unambiguous offset or UTC conversion.
