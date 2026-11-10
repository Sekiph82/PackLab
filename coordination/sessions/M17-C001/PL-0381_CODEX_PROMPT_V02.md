# PL-0381 — Codex Prompt V02

Task: **Cover disk-full and low-space handling safely**  
Milestone: **M17** · Cycle: **M17-C001**

V02 supersedes V01 after inspection found the project authority write boundary had no injectable low-space preflight and exposed a raw `ENOSPC` publish failure. The gap was recorded in `PL-0381_IMPLEMENTATION_GAP_V01.md` before runtime changes.

## Scope

- Add a bounded, injectable free-space check before publishing project authority state. Do not touch real disk limits in tests.
- Translate `ENOSPC` raised during the authority publish step into an actionable project diagnostic while preserving the last authoritative revision.
- Add tests with a fake zero-space provider and injected authority-publish `ENOSPC`; verify authority, state, raw capture bytes and temporary-file cleanup.
- Keep later compatibility-mirror recovery behavior intact. The preflight reserve cannot eliminate races or guarantee subsequent mirror writes.
- Do not add broad storage cleanup or delete pre-existing project data.

## Validation timing

- Defer pytest/Tester/lint/typecheck to the M17 milestone-end batch. Add regression tests now without executing them.
- Write `PL-0381_CODEX_LOG_V02.md`; retain V01 prompt/criteria and gap chronology.
