# PL-0436 Validation Criteria V08 — Offline CPU Worker

1. `VGGTSubprocessWorkspaceEngine` checks the pinned code/checkpoint/runtime metadata without importing torch, loading checkpoint bytes or constructing VGGT.
2. The engine launches only after the existing lazy RAM guard has admitted the physical-memory budget; the worker enforces the exact pinned code revision, checkpoint byte size/SHA-256, and ordered input image byte digests.
3. The child process receives offline Hub/Transformers settings, has no Hub token in its environment, uses the streaming loader, and exposes no local paths in result/error JSON.
4. Request/result sizes, image count, point count, output size, cancellation and process timeout are bounded. Malformed records, nonfinite camera values, out-of-order cameras and unsafe point-cloud artifacts fail closed.
5. Temporary request/result data is removed. Only explicitly cleanup-marked, regular files below the configured runtime output root are removed on success, cancellation, and failure; other artifacts remain.
6. Focused synthetic worker/protocol/cleanup and reconstruction tests, targeted Ruff, JSON/log digest verification, and `git diff --check` pass.
7. No real model/checkpoint load or inference, network/download, Actions/paid CI, PR, source push to `main`, native/Installer build, or release claim occurs. Record live RAM and local-only state.
