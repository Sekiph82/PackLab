# M16-C001-R08 - Authority Sync + Hard Disk Budget + PL-0350 V07 Continuation Audit Criteria V15

All criteria mandatory.

## Authority

1. Codex fetches origin and reads canonical tracker from `git show origin/main:TASKS.md`.
2. Stale raw/local TASKS content cannot override fetched origin/main.
3. Dirty/unpublished work is preserved non-destructively.
4. Master log records `AUTHORITY_SYNC_PASS` with remote/task identity.

## Hard disk budget and optimization

5. Heavy local work requires >=40 GiB free on C:.
6. Full local pytest uses a checked-in wrapper with one explicit basetemp.
7. The wrapper live-monitors basetemp and aborts above 4 GiB with `PYTEST_DISK_BUDGET_EXCEEDED`.
8. Total disposable PackLab temp/build/staging footprint is kept <=8 GiB during local work, excluding active worktree and protected current+previous OWNER DEV.
9. Completed disposable PackLab footprint is <1 GiB at child handoff unless a documented active artifact is required.
10. No single generated test fixture/tree exceeds 2 GiB without explicit justified exception.
11. Tests do not recursively duplicate the full repo, .venv, OWNER DEV runtime or package caches per test.
12. Pathological disk-producing fixtures are identified and refactored to minimal/shared/sparse/in-memory fixtures where valid.
13. A disk-optimization report identifies top temp producers and the fixes applied.
14. Completed stale PackLab pytest temp trees are removed after process-ownership checks.
15. PackLab AppData/OWNER DEV cleanup removes only proven unused generated staging/releases/logs while retaining current + one previous-good runtime.
16. Local PyInstaller/OCP/OCCT/source-extraction/installer/test staging is removed immediately after required evidence is retained.
17. Heavy controlled OCP/OCCT source build is not repeated locally unless specifically required; hosted CI remains the normal path.
18. Completed Codex PackLab worktrees are removed only when clean + inactive + published/reachable; dirty/active/unpublished worktrees are preserved.
19. Worktree retirement uses git worktree remove/prune, not blind filesystem deletion.
20. `uv cache prune` runs after major local validation and its before/after size is recorded.
21. pip cache is reduced with supported commands only when over 2 GiB.
22. Hugging Face/Puppeteer/Codex runtime/unrelated caches and owner personal files are not auto-deleted.
23. A checked-in disk-hygiene helper provides allowlisted inventory/preflight/post-test/post-task modes and dry-run.
24. Every child log records free-space before/after, reclaimed bytes, pytest peak, disposable PackLab peak, cleanup categories, retained worktrees and locked paths.
25. Another 65 GB pytest runaway is structurally prevented, not merely cleaned afterward.

## M16 continuation

26. Working Desktop PackLab.exe remains healthy.
27. PL-0350 V07 uses dedicated controlled-runtime producer with explicit N_PROC=4 and separate packaging job.
28. Exact native-input cache is fail-closed validated; packaging never rebuilds OCP/OCCT.
29. Cache-miss and verified cache-hit hosted paths both pass.
30. PL-0350 green requires zero unresolved redistribution/source/notice items, green packaged capability smoke and unsigned installer.
31. PL-0351 starts only after PL-0350 is green and validates the exact clean-installed artifact.
32. PL-0352 through PL-0367 run only after PL-0351 green, in order.
33. PL-0368 remains DEFERRED_POST_M17; M17 does not start.
34. Owner handoffs/logs use GitHub HTTPS links.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_AUTHORITY_HARD_DISK_BUDGET_PL0350_V07_CONTINUATION_CODEX_PROMPT_V15.md
