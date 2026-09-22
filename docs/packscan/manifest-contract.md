# PackScan manifest contract 1.0

`manifest.json` is the package index and is validated against
`schemas/packscan/manifest.schema.json`. It is intentionally strict:
unknown properties are rejected, timestamps must be UTC ISO-8601 values with a
`Z` suffix, and all payload paths are relative normalized ZIP paths.

The manifest identifies the capture with a stable `capture_id`, records the
iOS device summary and versioned capture mode, and declares every package file
with its role, authority, byte length, media type where applicable, and
lowercase SHA-256 digest. The checksum canonicalization identifier
`sha256_32_bytes_lowercase_hex_64_chars_v1` means exactly one 32-byte SHA-256
digest rendered as 64 lowercase hexadecimal characters; it is not 64 digest
bytes. `source_evidence.immutable` is always `true`;
previews, masks, thumbnails, and diagnostics are `derived` and cannot replace
source images or measurement truth.

`schema_version` is the schema contract version and is not inferred from a
filename. A future major/minor structure is rejected until an explicit schema
revision declares compatibility. A local time such as `2026-09-22 12:00:00`
is invalid because it has no unambiguous offset or UTC conversion.

## Capture-mode variants

`capture_mode` is a tagged union, not an arbitrary parameter blob. PackScan
1.0 accepts only the explicit version-1 variants `freehand`, `guided_orbit`,
and `turntable`; an unknown mode or future version requires a schema revision.
Each variant rejects fields belonging to another mode.

- `freehand` shares only the mode/version fields and may state
  `parameters.operator_guidance: none`. It describes operator-directed views;
  it does not promise coverage or an orbit algorithm.
- `guided_orbit` requires `orbit_axis: subject_vertical` and a bounded
  `coverage` record. `target_sector_deg` is a positive exclusive-360-degree
  target, and `minimum_view_count` is an integer lower bound. These are
  capture metadata boundaries, not proof that the target was achieved.
- `turntable` requires an integer zero-based `frame_index`, positive
  `frame_count`, and `angle_deg` in `[0, 360)`. Angles use degrees and the
  frozen convention `clockwise_from_reference`; the index identifies the
  frame's position in the declared sequence. The metadata does not implement
  motor control or infer an angle from pixels.

Adding a future mode requires a new versioned schema variant with explicit
fields and tests. Unvalidated `parameters` members and mixed-mode combinations
are rejected.
