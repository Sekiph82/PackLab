# PL-0379 — Validation Criteria V02

1. Compressed package size is rejected above 512 MiB before ZIP parsing.
2. ZIP entry count is bounded to 1,024 before `ZipFile` central-directory materialization; ZIP64/multi-disk layouts fail closed.
3. Every member is limited to 64 MiB, control entries to 4 MiB, and the actual total expanded stream to 512 MiB. Declared ZIP sizes are checked before reading and actual bytes while streaming.
4. The writer refuses to produce packages above the same entry, control, expanded-content, and compressed-output limits.
5. The real import boundary rejects an oversized package without publishing raw/extracted data; quarantine preserves only within a fixed byte cap and otherwise records `package_preserved=false`.
6. Extraction uses the bounded loader and verifies the second snapshot against the validated checksum/manifest before publishing.
7. Existing malformed, truncated, traversal, checksum, and quarantine behaviors remain covered by current grouped test sources.
8. New resource tests use small fixtures/monkeypatched limits, not large allocations. Test execution status is reported truthfully and remains unrun after this remediation.
