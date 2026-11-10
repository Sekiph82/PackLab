# PL-0380 — Codex Prompt V01

Task: **Cover interrupted reconstruction jobs and safe resume/retry**  
Milestone: **M17** · Cycle: **M17-C001**

Add deterministic tests using injected/fake COLMAP and OpenMVS stage executors to interrupt a multi-stage job and exercise resume/retry from the last valid stage. Assert completed artifacts are not overwritten and incomplete output is not promoted. Do not launch paid/hosted CI or real external binaries in this child. Report missing behavior before any production change. Defer test execution to M17 milestone end. Write `PL-0380_CODEX_LOG_V01.md`.
