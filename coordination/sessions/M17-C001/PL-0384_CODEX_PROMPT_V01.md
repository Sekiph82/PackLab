# PL-0384 — Codex Prompt V01

Task: **Cover project migration across schema/app versions**  
Milestone: **M17** · Cycle: **M17-C001**

Add migration regression tests through the public project import/migration boundary using small disposable fixtures. Cover supported previous versions, deterministic forward migration, unknown future versions, malformed data and preservation of source bytes/state. Do not edit owner project files. Report migration gaps before production changes. Defer test execution to M17 milestone end. Write `PL-0384_CODEX_LOG_V01.md`.
