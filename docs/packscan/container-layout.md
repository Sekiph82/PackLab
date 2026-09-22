# PackScan 1.0 container layout

`.packscan` is a deterministic ZIP package. The package is an evidence
container, not a mutable working directory: original capture bytes and their
metadata remain authoritative, while masks, previews, and diagnostics are
derived and may be omitted or regenerated.

## Required entries

| Entry | Authority | Rule |
| --- | --- | --- |
| `manifest.json` | authoritative contract | UTF-8 JSON, schema `1.0.0`; declares every payload and its SHA-256 |
| `metadata/photos.json` | authoritative capture metadata | one deterministic record per image path and sequence number |
| `checksums.json` | integrity index | SHA-256 entries for every file except this index |
| `images/` | authoritative source evidence | at least one original image file; paths are declared in the manifest |

`images/` is a required namespace, not a literal directory entry. Empty ZIP
directory entries are forbidden. The image payloads are never replaced by a
preview or a re-encoded derivative.

## Optional namespaces

`metadata/` may contain additional source metadata, `calibration/` may contain
calibration provenance, and `masks/`, `previews/`, and `diagnostics/` may hold
derived artifacts. A missing optional artifact is valid when the manifest does
not declare it. A declared artifact that is missing, duplicated, or has the
wrong checksum is invalid.

## Path, ordering, and compression rules

Paths use UTF-8 forward slashes, are relative, and contain no empty, `.` or
`..` component, leading slash, backslash, drive prefix, or case-insensitive
duplicate. A path is normalized before comparison; duplicate names are always
rejected. Directory entries are rejected. The writer orders the three control
entries first and all remaining normalized paths lexicographically by UTF-8
bytes. Every deterministic writer MUST set the ZIP central-directory DOS
timestamp of every entry to exactly `1980-01-01T00:00:00` (UTC-independent
calendar value; ZIP stores this as date `1980-01-01` and time `00:00:00`).
Timestamp-related ZIP extra fields MUST be omitted, including extended/UT
(`0x5455`) and NTFS (`0x000a`) timestamp fields. This exact string and the
explicit omission rule are implementable by both Python and Swift without
platform-local time conversion. The reader validates the path and duplicate
rules before reading content.

## Compatibility and authority

The major version is incompatible by default. A future major version is
rejected rather than guessed. An older major version requires an explicit,
versioned migration before it can become a current package. Within major `1`,
only structures named by the schema and layout are accepted; unknown required
structures are an error. Source evidence is immutable by contract, and
previews, masks, and diagnostics never replace measurement truth.
