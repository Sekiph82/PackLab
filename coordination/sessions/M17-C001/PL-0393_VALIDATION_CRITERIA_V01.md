# PL-0393 — Validation Criteria V01

1. A single identified PackLab source commit has successful Windows and macOS/iOS Actions runs.
2. Each run produced the expected artifact; artifact identity/hash is recorded and bound to the commit.
3. No unrelated historical run substitutes for the intended commit.
4. If the owner Actions moratorium or unsafe publication state prevents this, leave incomplete and record the exact blocker without dispatching.
