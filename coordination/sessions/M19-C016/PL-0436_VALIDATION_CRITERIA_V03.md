# PL-0436 Validation Criteria V03 — VGGT Asset and Coordinate Bridge

V03 extends the V02 adapter contract. Owner VGGT/Hugging Face access and local-use approval are complete; do not request them again.

1. Source resolution requires one expected SHA-256 per declared image asset, preserves input order, rejects missing/extra digest entries, traversal, reparse escapes, non-files and digest/stat changes, and leaves source bytes untouched.
2. VGGT OpenCV world-to-camera extrinsics are converted to PackScan camera-to-world convention using documented axis transforms; pixel intrinsics account for the declared padding/resizing transform and top-left-pixel-center origin. Invalid matrices/dimensions fail closed.
3. Derived publication writes only beneath a new `derived/reconstruction/<revision>` path, verifies artifact digests while copying, rejects overwrite/path escape/symlink components, writes a canonical manifest atomically, and removes only its own staging directory on failure.
4. Published metadata preserves exact project/source identity, uses `NEURAL_EXPERIMENTAL` and `RECONSTRUCTION_OBSERVATION`, and cannot claim `METRIC_VERIFIED`.
5. Tests use synthetic images/matrices/artifacts only; they must not load VGGT or checkpoint weights and must include traversal, digest mismatch, source immutability, camera conversion, overwrite and failed-publication boundaries.
6. Focused local tests, targeted Ruff, job JSON/log hash verification, and `git diff --check` pass.
7. Zero Actions/paid CI, no PR, no source push to `main`, no native/Installer build, and no release-readiness claim. Real inference remains blocked until an image/runtime adapter is wired and sufficient physical RAM is measured.
