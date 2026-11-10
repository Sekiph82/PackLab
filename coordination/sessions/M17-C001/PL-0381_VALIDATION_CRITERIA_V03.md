# PL-0381 — Validation Criteria V03

1. `OSError` and another ordinary free-space-provider exception fail through actionable `ProjectError` before authority publication.
2. Bool, negative integer, float, and `None` provider results fail closed before authority publication.
3. Each case preserves authority/state bytes, revision, immutable raw input and task-owned temp-file state.
4. Existing zero-space, publish-time `ENOSPC`, and post-authority mirror-recovery cases remain in the grouped test suite.
5. New tests use disposable `tmp_path` projects only; no tests execute in this child.
