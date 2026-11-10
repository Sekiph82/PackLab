# PL-0394 — Codex Prompt V01

Task: **Complete security/secrets audit of the public repository**  
Milestone: **M17** · Cycle: **M17-C001**

Audit public GitHub `main` and M17 source changes for secrets/protected data, unsafe archive/path handling, license/provenance and integrity boundaries, dependency/security claims, and accidental CI/publication risk. An independent security reviewer must inspect the actual diff/evidence after implementation; Codex's own scan is not an independent verdict. Do not print secrets or private data. Respect no-Actions/no-paid-CI policy. Keep local versus public commit coverage explicit. Write `PL-0394_CODEX_LOG_V01.md` after the audit evidence is collected.
