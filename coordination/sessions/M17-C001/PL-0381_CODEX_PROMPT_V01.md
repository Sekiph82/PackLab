# PL-0381 — Codex Prompt V01

Task: **Cover disk-full and low-space handling safely**  
Milestone: **M17** · Cycle: **M17-C001**

Add deterministic tests through injected storage/free-space providers and bounded temporary directories for low-space and write-failure behavior. Verify actionable diagnostics, no partial final publication, and safe cleanup restricted to task-owned temporary output. Never fill the real C: drive or alter unrelated owner files. Report missing runtime behavior before implementation changes. Defer tests to M17 milestone end. Write `PL-0381_CODEX_LOG_V01.md`.
