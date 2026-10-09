# M16-C001-R08 / V16 ChatGPT audit criteria

Authoritative independent review reference:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001-R08_CHATGPT_AUDIT_V01.md

**ALL required for R08 hygiene PASS; PL-0350 has separate hard gates.**

1. Latest `origin/main` and its `TASKS.md` fetched, M16-C001-R08/V16 verified; no changes to owner dirty Desktop tree, unrelated projects, audit verdicts or root TASKS.
2. >=40 GiB C: before heavy work; 4 GiB pytest basetemp limit, 2 GiB fixture limit and 8 GiB total disposable PackLab cap retained; no inflated exceptions.
3. Aggregate budget is recomputed *during* test lifetime across **all** allowlisted disposable roots; a non-pytest staging-root growth test demonstrates this. Locked/unreadable paths fail closed and report reason, rather than count as zero and pass.
4. Live stdout/stderr handling never passes null `Task` to `WaitAny`; asymmetric EOF, quiet process and correct exit-code propagation are covered by executed test evidence.
5. Real behavioral tiny-limit tests demonstrate quota violation messages/codes, targeted child stop, no unrelated-process termination, correct marked-basetemp finally cleanup and failure-mode reporting. Static token asserts alone are inadequate. No multi-gigabyte tests.
6. Monitoring remains responsive and bounded on realistic fixture counts; no repeated whole shared uv cache walk.
7. Before/after and peak disposable bytes and C: free space recorded in child and master handoff; protected OWNER DEV runtimes not counted as disposable.
8. Global uv cache with active Godot/Blender/MCP users: `DEFERRED_SHARED_UV_CACHE_ACTIVE` with evidence is an **authorized safe exception** to former V15 must-prune gate. No unrelated process kill, forced prune, `uv cache clean`, permission bypass or unbounded size scan. When genuinely idle, supported `uv cache prune` runs with truthful bounded before/after, if measurable. Deferred shared-cache condition does NOT block hosted PL-0350 CI.
9. Legacy AppData: read-only per-directory inventory; safe targeted, verified removals only with opt-in and permitted policy. If ambiguity/regeneration, retain with `DEFERRED_PROTECTED_UNVERIFIED`, measured or explicitly unknown bytes. Retention not misreported as successful deletion/0 total disk use.
10. Protect active and previous-good OWNER DEV runtime, desktop native EXE, user files, dirty/active/unpublished worktrees, unrelated caches and the 13 historical startup logs if still diagnostically relevant. No broad deletion of entire old tree under an automatic denial.
11. Focused behavioral tests + Ruff + PowerShell parse + diff clean; if a full local suite is run, it MUST use safe wrapper and live quotas.
12. Published implementation/log and refreshed owner EXE matching the implementation source, hash and usable window evidence where actually tested; no claim of standalone install.
13. PL-0350 V07 can begin only if PackLab-controlled Phase 0 safety fixes pass; no prerequisite to interrupt shared-cache users.
14. PL-0350 V07 independent gates: dedicated `N_PROC=4` producer, exact sealed cache with hosted miss and hit, separate no-OCP-rebuild packaging job, zero unresolved redistribution issues, shipped capability smoke, real unsigned installer. Stop truthfully otherwise.
15. PL-0351 begins only after actual cleared installer, fresh Windows isolated install and dev-path-sanitation QtCore/QtPdf/OCP/Open3D PASS. PL-0352–PL-0367 strictly sequenced. PL-0368 deferred; M17 not begun.
16. Each child: separate log, GitHub HTTPS evidence/commits/actions, source parity and OWNER DEV refresh. All blocked conditions recorded honestly.

Verdict must distinguish **R08 hygiene PASS** from **PL-0350/whole M16 PASS**. Do not check off PL-0350 or M16 for partial hygiene implementation.

Master V16:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_R08_DISK_REMEDIATION_PL0350_V07_CONTINUATION_CODEX_PROMPT_V16.md
