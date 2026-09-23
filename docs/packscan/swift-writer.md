# Swift PackScan writer

`PackLabCapture/PackScan/PackScanWriter.swift` is the iOS-side package
finalizer. It accepts contract JSON and payload bytes from Capture services;
it does not import camera, ARKit, or NextLevel APIs. The Python PackScan
validator and the versioned JSON schemas remain cross-platform truth.

The writer canonicalizes manifest and checksum JSON as sorted UTF-8 JSON with
a trailing newline, computes lowercase SHA-256 for every file except
`checksums.json`, orders `manifest.json`, `metadata/photos.json`,
`checksums.json`, then remaining paths lexicographically, and emits ZIP entries
with deflate compression, no extra fields, and the frozen 1980-01-01 DOS
timestamp. It rejects unsafe paths, undeclared or missing payloads, size/hash
mismatches, missing image/photo metadata namespaces, and schema/checksum
contract drift.

ZIP headers encode time `0x0000`, date `0x0021`, method `8`, and UTF-8
general-purpose bit `0x0800` in both local and central headers. The writer uses
zlib `deflateInit2_` with `Z_BEST_COMPRESSION` and negative `MAX_WBITS` so the
payload is raw DEFLATE suitable for ZIP method 8, not zlib or gzip framed data.

Finalization writes to a unique `.partial` file in the destination directory
using atomic Data write semantics and moves it into place only after the ZIP
bytes are complete. An existing destination is not overwritten, and a failed
write removes the partial file; an interrupted write therefore cannot appear
as a complete `.packscan` package.

`tests/fixtures/packscan/swift-writer-contract-fixture.json` is deterministic
static evidence for later macOS/Xcode cross-language tests. Windows validation
here is limited to source inspection, project-file linkage, schema-compatible
fixture inspection, and the Python reader; native Swift compilation and iOS
device execution are unavailable and are not claimed.

`tests/packscan/test_swift_compatibility.py` treats the committed fixture as
the deterministic Swift-output contract: it validates the equivalent package
with Python, checks ZIP layout/checksum/photo-metadata semantics, and mutates
only the manifest's authoritative image hash to prove the Python validator
rejects a semantically corrupt package. It also parses byte-level ZIP local and
central header fields from the constants in the Swift source to lock the
timestamp, method, flags, CRC/size slots and omitted extra fields. The future
macOS/Xcode boundary is a native test that invokes this writer and feeds its
actual bytes to the same Python validator; that test is intentionally not
simulated on Windows.
