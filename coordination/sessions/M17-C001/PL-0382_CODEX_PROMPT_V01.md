# PL-0382 — Codex Prompt V01

Task: **Cover crash/restart project recovery**  
Milestone: **M17** · Cycle: **M17-C001**

Add deterministic persistence/recovery tests using a temporary synthetic PackLab project. Simulate interruption between durable state transitions, restart through the actual recovery boundary, and verify only committed/checksummed state is restored. Preserve owner projects; do not kill or modify a live application. Report unavailable crash-injection hooks before production changes. Defer tests to M17 milestone end. Write `PL-0382_CODEX_LOG_V01.md`.
