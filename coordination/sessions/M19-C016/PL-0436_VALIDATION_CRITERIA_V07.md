# PL-0436 Validation Criteria V07 — Streaming Checkpoint Loader

1. The loader validates file type, exact size, and SHA-256 before importing/opening safetensors tensors.
2. The loader imports torch/safetensors lazily, never uses `load_file`, never builds a full weights dictionary, and loads only CPU tensors.
3. Exact state keys, tensor shapes, and dtypes are required; key or digest mismatches fail before tensor copying.
4. A generated tiny synthetic safetensors file loads into a small CPU module and produces matching parameter values.
5. Tests do not read or load the real VGGT checkpoint and do not construct the actual VGGT model.
6. Focused synthetic/runtime/adapter tests, targeted Ruff, job JSON/log SHA validation, and `git diff --check` pass.
7. No Actions/paid CI, PR, source push to `main`, native/Installer build, or release claim; owner access/local-use approval remains complete.
