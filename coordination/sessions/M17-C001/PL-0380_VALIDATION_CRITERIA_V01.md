# PL-0380 — Validation Criteria V01

1. An interrupted fake reconstruction job has a deterministic cancelled/failed state.
2. Retry resumes only from validated checkpoints and preserves already completed immutable artifacts.
3. Partial outputs cannot be published as a completed Scan Master.
4. No real paid or hosted compute is used.
5. Test execution is deferred to the M17 milestone-end batch.
