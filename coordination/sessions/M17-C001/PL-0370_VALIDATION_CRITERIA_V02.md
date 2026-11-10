# PL-0370 — Validation Criteria V02

1. Exact archive identity is pinned to reviewed official URL, byte count and SHA-256.
2. Archive and output paths fail closed on symlink/junction/reparse traversal and remain under the dataset root.
3. Extracted member records are verified byte-for-byte against named archive members.
4. Interrupted extraction leaves no partial final path; existing valid files are verified rather than overwritten.
5. The standalone local corpus validator passes all 2 objects, 10 model files and 30 JPEGs after these checks.
6. Regression test sources cover the security boundaries; current post-remediation test execution is explicitly reported (not inferred from the earlier batch).
7. Full data remain outside Git; attribution, CC BY 4.0 and nonphysical measurement/photo-registration caveats remain intact.
