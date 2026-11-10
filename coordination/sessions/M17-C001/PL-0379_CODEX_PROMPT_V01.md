# PL-0379 — Codex Prompt V01

Task: **Cover corrupt `.packscan` import and quarantine**  
Milestone: **M17** · Cycle: **M17-C001**

Add negative regression tests for truncated, corrupt and path-hostile `.packscan` inputs through the real PackLab import boundary. Verify fail-closed rejection, bounded resource use, no extraction outside the import root, and quarantine/diagnostic behavior where supported. Use disposable test fixtures only; never mutate owner workspaces or existing scans. Report missing quarantine behavior without claiming it exists. Defer tests to M17 milestone end. Write `PL-0379_CODEX_LOG_V01.md`.
