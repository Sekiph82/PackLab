# PL-0383 — Codex Prompt V01

Task: **Cover missing/wrong external-engine diagnostics**  
Milestone: **M17** · Cycle: **M17-C001**

Add tests around the real external-engine capability/version probes using fake or isolated executables. Cover missing binary, wrong reported version, malformed version response and a valid pinned version. Assert deterministic actionable diagnostics and fail-closed stage readiness. Do not install or download engines in this task. Defer test execution to M17 milestone end. Write `PL-0383_CODEX_LOG_V01.md`.
