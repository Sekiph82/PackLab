# PL-0383 — Codex Prompt V02

Task: **Cross-platform engine probe failure diagnostics**  
Milestone: **M17** · Cycle: **M17-C001**

V02 repairs a source-review finding in the fake executable fixtures. On POSIX, the engine probe checks executable permission before invoking its injected runner; fixture files must therefore receive owner execute permission so tests exercise the intended injected result rather than short-circuiting as UNEXECUTABLE. Preserve Windows behavior and do not execute/install any engine.

## Scope

- Use a small helper to create disposable executable placeholders with user execute permission on non-Windows hosts.
- Apply it to tests that expect the injected runner to determine the probe result, including wrong argv, supported/unsupported versions, malformed banners, OpenMVS component readiness and injected runner failure.
- Keep missing-path behavior unchanged. Do not chmod the host's real tools or alter production probe logic.
- Add no task-specific test execution. Keep validation deferred to the M17 grouped checkpoint.

Write `PL-0383_CODEX_LOG_V02.md` after independent source review; explicitly state tests were not run.
