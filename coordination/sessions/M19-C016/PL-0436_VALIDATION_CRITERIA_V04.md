# PL-0436 Validation Criteria V04 — Injected Workspace Runtime

1. The workspace runtime composes exact-digest image resolution, ordered engine input, coordinate normalization, and safe derived-artifact publication.
2. The engine is never called when source resolution fails or cancellation is already set. Cancellation after engine return prevents publication.
3. The adapter rejects camera records with missing, extra, duplicate, or invalid image identity and rejects malformed camera/inference output.
4. The returned `ReconstructionOutputManifest` retains the exact project/source/configuration identity, PackScan camera convention, normalized cameras, artifact paths and digests, and non-authoritative scale/authority.
5. Synthetic tests exercise engine invocation order, failure boundaries, camera normalization, output publication, and local-path privacy. Tests must not load or execute VGGT/checkpoint weights.
6. Focused neural IO/backend tests, targeted Ruff, job/log SHA validation, and `git diff --check` pass.
7. No GitHub Actions/paid CI, PR, source push to `main`, native/Installer build, or release claim. Real inference remains pending sufficient physical RAM and a concrete engine implementation.
