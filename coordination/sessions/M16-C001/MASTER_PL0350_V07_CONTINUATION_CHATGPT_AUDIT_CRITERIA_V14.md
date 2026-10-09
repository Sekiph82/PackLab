# M16-C001-R08 - Authority Sync + Disk Hygiene + PL-0350 V07 Continuation Audit Criteria V14

All criteria mandatory.

## Canonical authority sync

1. Codex records current worktree path and status before sync.
2. Codex runs `git fetch --prune origin`.
3. Canonical tracker authority is read with `git show origin/main:TASKS.md` or equivalent GitHub repository-file API, not a cached raw URL.
4. Local stale TASKS content never overrides fetched `origin/main`.
5. Current remote tracker must authorize M16-C001-R08/V14 or a newer explicit superseding continuation before implementation.
6. Unpublished/dirty local work is preserved; no destructive reset is used to achieve parity.
7. If needed, a clean managed worktree from current `origin/main` is used instead of overwriting dirty work.
8. Master log records canonical origin/main SHA, TASKS blob SHA, milestone/task identity, worktree path/status, and `AUTHORITY_SYNC_PASS`.
9. A newer origin/main is allowed if its canonical TASKS still authorizes this scope; a genuinely changed task stops with `CANONICAL_TASK_CHANGED`.

## Permanent local disk hygiene

10. Heavy local commands require a C: free-space preflight with a 40 GiB minimum.
11. Cleanup is allowlist-based and never targets owner Documents/Videos/Pictures/Downloads/general Desktop content.
12. PackLab source, active/dirty worktrees, Desktop PackLab.exe, active OWNER DEV runtime and one previous-good runtime are protected.
13. A checked-in disk-hygiene helper exists with dry-run and preflight/post-test/post-task behavior or equivalent.
14. A checked-in full-test wrapper creates an explicit unique pytest basetemp and removes it in finally while preserving the pytest exit code.
15. Completed PackLab pytest basetemps are removed immediately; failures retain only compact required diagnostics.
16. Local PyInstaller/build/source-extraction/temp installer trees are removed after required evidence is retained.
17. OWNER DEV retention is bounded to current + one previous-good plus stable launcher/branding.
18. Completed Codex PackLab worktrees are removed only after clean-status + published/reachable-commit + inactive verification.
19. Worktrees are retired using Git worktree commands, never blind filesystem deletion.
20. `uv cache prune` is used after major local validation; routine `uv cache clean` is forbidden.
21. Hugging Face/Puppeteer/Codex runtime/unrelated caches are not auto-deleted.
22. Every child log records disk free before/after, reclaimed bytes, cleanup categories, retained worktrees and locked paths.
23. Heavy PL-0350 V07 work resumes only after >=40 GiB free, otherwise it stops truthfully with `LOCAL_DISK_SPACE_BLOCKED`.

## PL-0350 V07 and continuation

24. Working native Desktop PackLab.exe remains healthy for owner use.
25. PL-0350 V07 uses a dedicated controlled-runtime producer job with explicit N_PROC=4 and separate packaging job.
26. Controlled runtime cache key is based on exact native build inputs rather than ordinary PackLab commit identity.
27. Cache hit is fail-closed validated against source-lock/build-contract/file digests before use.
28. Same-run artifact transfer separates cache authority from packaging consumption.
29. Packaging job never rebuilds OCP/OCCT.
30. First cache-miss producer run finishes within hosted job limit.
31. Second run/rerun proves verified cache HIT without pywrap rebuild.
32. PL-0350 green requires zero unresolved shipped files/components, zero missing notices/source packages, zero forbidden Qt modules, green packaged capability smoke and unsigned installer.
33. PL-0351 starts only after PL-0350 V07 is green.
34. PL-0351 tests the exact installed artifact in a separate sanitized Windows job and fails hard on native loader/procedure/entry-point errors.
35. PL-0352 through PL-0367 begin only after PL-0351 is green and execute in exact order.
36. Every completed child publishes implementation/evidence and distinct GitHub-visible child log.
37. Owner handoffs/logs use clickable GitHub HTTPS links; local C:\ paths are not accepted as owner handoff references.
38. OWNER DEV never regresses to Desktop LNK/PowerShell.
39. No private-data/secrets/signing leakage, tag/GitHub Release/V0.1 publication, M17 or PL-0368 execution.
40. PL-0368 remains DEFERRED_POST_M17.
41. Real blocker stops truthfully at AWAITING_MILESTONE_AUDIT.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_AUTHORITY_DISK_HYGIENE_PL0350_V07_CONTINUATION_CODEX_PROMPT_V14.md
