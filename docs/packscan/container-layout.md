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

`checksums.json` uses `schemas/packscan/checksums.schema.json` and stores one
lowercase 64-character hexadecimal SHA-256 digest for every other ZIP file,
including `manifest.json`. The writer uses canonical UTF-8 JSON and the frozen
`sha256_32_bytes_lowercase_hex_64_chars_v1` identifier. A missing, extra,
malformed, or mismatched index entry is a package failure.

## Optional namespaces

`metadata/` may contain additional source metadata, `calibration/` may contain
calibration provenance, and `masks/`, `previews/`, and `diagnostics/` may hold
derived artifacts. A missing optional artifact is valid when the manifest does
not declare it. A declared artifact that is missing, duplicated, or has the
wrong checksum is invalid.

Preview and thumbnail payload declarations use `kind: preview` or
`kind: thumbnail`, `authority: derived`, `required: false`, a `previews/` or
`thumbnails/` path, and an image media type (`image/jpeg`, `image/png`, or
`image/webp`). Diagnostics declarations use `kind: diagnostics`,
`authority: derived`, `required: false`, a `diagnostics/` path, and
`application/json`. Every declared derived payload still carries its exact
byte size and lowercase SHA-256 in the manifest; omission is safe and does
not remove or replace original images or measurement truth.

Diagnostics JSON is validated against
`schemas/packscan/diagnostics.schema.json`. It is a bounded list of codes,
severity, redacted messages, and numeric counters/timings. Credentials,
credential-like fields, and private local path segments are prohibited. A
diagnostic may describe a derived/debug condition but cannot become an
authoritative source by changing its manifest kind.

## Path, ordering, and compression rules

Paths use UTF-8 forward slashes, are relative, contain at most 1,024 Unicode
code points and 4,096 UTF-8 bytes, and contain no control character below
U+0020, empty, `.` or `..` component, leading slash, backslash, drive prefix,
or case-insensitive duplicate. A path is normalized before comparison;
duplicate names are always rejected. Directory entries are rejected. The writer orders the three control
entries first and all remaining normalized paths lexicographically by UTF-8
bytes. Every deterministic writer MUST set the ZIP central-directory DOS
timestamp of every entry to exactly `1980-01-01T00:00:00` (UTC-independent
calendar value; ZIP stores this as date `1980-01-01` and time `00:00:00`).
Timestamp-related ZIP extra fields MUST be omitted, including extended/UT
(`0x5455`) and NTFS (`0x000a`) timestamp fields. This exact string and the
explicit omission rule are implementable by both Python and Swift without
platform-local time conversion. The reader validates the path and duplicate
rules before reading content.

## V1 implementation resource ceiling

The current PackLab V1 reader/writer accepts packages up to 512 MiB compressed,
with at most 1,024 ZIP entries, 64 MiB per entry, 4 MiB for each control entry
(`manifest.json`, `checksums.json`, and `metadata/photos.json`), and 512 MiB
total expanded content. Readers check the ZIP entry count before materializing
the central directory and enforce declared and actual decompressed byte limits.
Packages beyond these limits are rejected with a stable resource-limit error;
this is a software safety ceiling, not a camera or physical packaging limit.

The bounded V1 reader accepts single-disk, non-ZIP64 archives with no archive
preamble, central-directory extra fields, or member/archive comments.
It verifies the end record against the complete central-directory record
sequence before asking the ZIP library to materialize entries. These framing
rules keep the preflight bounded and match PackLab's deterministic Python and
iOS writers.

## Compatibility and authority

The major version is incompatible by default. A future major version is
rejected rather than guessed. An older major version requires an explicit,
versioned migration before it can become a current package. Within major `1`,
only structures named by the schema and layout are accepted; unknown required
structures are an error. Source evidence is immutable by contract, and
previews, masks, and diagnostics never replace measurement truth.
