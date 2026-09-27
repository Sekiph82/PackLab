# M06-R01 — ChatGPT Remediation Audit Criteria V01

Scope: **PL-0138, PL-0140, PL-0141, PL-0144, PL-0145, PL-0146, PL-0147, PL-0148, PL-0149**

Source audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/CHATGPT_AUDIT_V01.md

All criteria are mandatory.

1. Repository safety is preserved. Before material work, fetch `origin/main`, inspect divergence and worktree state, and never reset, rebase, force-push, destructively clean or discard owner work.
2. Any existing local-only commits for `PL-0145_CODEX_LOG_V01.md`, `PL-0149_CODEX_LOG_V01.md` and `MASTER_CODEX_LOG_V01.md` are published exactly as existing evidence when safe. Do not recreate or rewrite them merely to make the audit pass.
3. M03–M05 remain accepted, PL-0068 remains OWNER_REQUIRED and M07 remains untouched.
4. Codex does not edit root `TASKS.md`, ChatGPT audit files or ChatGPT criteria files.
5. PL-0150 through PL-0157 are not started in this remediation.
6. PL-0138 production restore sanitizes saved geometry against the currently available screen/work area before applying it. Corrupt/future preference state still falls back safely. Add a production-seam test proving an off-screen saved window is restored to a usable location.
7. PL-0140 keeps `packlab_core.subprocess_runner` as the only process-cancellation authority. Add deterministic production-adapter coverage for `OwnedSubprocessJob` cancellation/cleanup and prove PackLab cancellation does not target unrelated processes.
8. PL-0141 diagnostics are reachable through the production Studio/project service seam and collect bounded build/runtime, active project summary, active jobs and recent structured errors without secrets, pairing codes, raw payloads or private absolute paths. Add production-seam tests.
9. PL-0144 route/workspace availability reflects ProjectManager open/closed state rather than widget-local shadow state. A blocked switch caused by active jobs must not publish/create a replacement project destination before the close policy is accepted.
10. PL-0146 editable state plus revision authority is transactionally crash-safe. An injected failure between state and metadata publication must leave the previously authoritative revision intact or deterministically recoverable, never silently expose mismatched state/revision.
11. PL-0147 preserves append-only logical history while publishing persistence atomically. Reopen must reject revision gaps/tamper/corrupt partial publication. Add injected-write-failure and revision-continuity tests.
12. PL-0148 recovery is integrated with ProjectManager/Studio lifecycle: open/start establishes recovery authority, abnormal reopen exposes classification/actions, accepted/discarded recovery is project-scoped, and clean close marks the session clean. Raw evidence remains untouched.
13. PL-0149 persists stale/invalid state across reopen, exposes an explicit deterministic query seam usable by UI badges/job planning, propagates direct/transitive invalidation, and detects missing/tampered upstream inputs. Add stale-reopen and query-seam tests.
14. Existing accepted PL-0135/0136/0137/0139/0142/0143 behavior remains unregressed.
15. The exact full locked suite exits 0. Relevant focused tests, Ruff, mypy where configured, compileall, project/static checks and `git diff --check` pass truthfully.
16. No new dependency is added unless necessary, declared, locked, reproducible and license-compliant.
17. Remediation evidence uses full GitHub URLs only. No abbreviated repository links or local-only filesystem paths appear in user-facing handoff artifacts.
18. Publish one remediation implementation/evidence commit set and a separate `M06-R01_CODEX_LOG_V01.md` log-only commit.
19. The remediation log lists every affected task, exact changed files, focused/full test results, commit SHAs, publication-recovery outcome and residual limitations.
20. The remediation log ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Closure requires independent ChatGPT `AUDITED_PASS`. Do not self-audit.
