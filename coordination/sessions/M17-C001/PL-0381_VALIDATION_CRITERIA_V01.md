# PL-0381 — Validation Criteria V01

1. Injected low-space/write-failure cases return a deterministic actionable state.
2. Partial artifacts are not published as complete outputs.
3. Cleanup is scoped to disposable task-created files and preserves prior outputs.
4. Tests do not consume substantial real disk or alter owner data.
5. Test execution is deferred to M17 milestone end.
