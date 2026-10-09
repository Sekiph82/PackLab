# M16-C001-R08 - Disk Hygiene + PL-0350 V07 Continuation Master Audit Criteria V13

All criteria mandatory.

## Permanent local disk hygiene

1. Disk hygiene is implemented as part of R08, not a separate milestone.
2. Heavy local commands require a C: free-space preflight with a 40 GiB minimum.
3. Cleanup is allowlist-based and never targets owner Documents/Videos/Pictures/Downloads/general Desktop content.
4. PackLab source, active/dirty worktrees, Desktop PackLab.exe, active OWNER DEV runtime and one previous-good runtime are protected.
5. A checked-in disk-hygiene helper exists with dry-run and preflight/post-test/post-task behavior or equivalent.
6. A checked-in full-test wrapper creates an explicit unique pytest basetemp and removes it in finally while preserving the pytest exit code.
7. Completed PackLab pytest basetemps are removed immediately; failure keeps only compact required diagnostics, not multi-GB trees.
8. Local PyInstaller/build/source-extraction/temp installer trees are removed after required evidence is retained.
9. OWNER DEV retention is bounded to current + one previous-good plus stable launcher/branding.
10. OWNER DEV logs are bounded to newest 20 and <=7 days except explicitly preserved unresolved-failure evidence.
11. Completed Codex PackLab worktrees are removed only after clean-status + published/reachable-commit + inactive verification; dirty/active/ambiguous worktrees are preserved.
12. Worktrees are retired using Git worktree commands, never blind filesystem deletion.
13. `uv cache prune` is used after major local validation; routine `uv cache clean` is forbidden.
14. pip cache is only purged/reduced via supported pip commands when above the documented threshold.
15. Hugging Face/Puppeteer/Codex runtime/unrelated caches are not auto-deleted.
16. Every child log records disk_free_before_bytes, disk_free_after_bytes, reclaimed_bytes, cleanup categories, retained worktrees and locked paths.
17. First hygiene execution safely removes stale PackLab pytest temp data and other proven reproducible PackLab artifacts without deleting personal files.
18. Heavy PL-0350 V07 work resumes only after >=40 GiB free, otherwise it stops truthfully with LOCAL_DISK_SPACE_BLOCKED.
19. Final master handoff proves no known completed PackLab pytest basetemp, removable completed worktree, or stale local build tree remains without documented active reason.

## PL-0350 V07 and continuation

20. Live TASKS authorizes R08; Codex does not edit root TASKS.
21. Working native Desktop PackLab.exe remains healthy for owner use.
22. PL-0350 V07 uses a dedicated controlled-runtime producer job with explicit N_PROC=4 and separate packaging job.
23. Controlled runtime cache key is based on exact native build inputs rather than ordinary PackLab commit identity.
24. Cache hit is fail-closed validated against source-lock/build-contract/file digests before use.
25. Same-run artifact transfer separates cache authority from packaging consumption.
26. Packaging job never rebuilds OCP/OCCT.
27. First cache-miss producer run finishes within hosted job limit.
28. Second run/rerun proves verified cache HIT without pywrap rebuild.
29. PL-0350 green requires zero unresolved shipped files/components, zero missing notices/source packages, zero forbidden Qt modules, green packaged capability smoke and unsigned installer.
30. PL-0351 starts only after PL-0350 V07 is green.
31. PL-0351 tests the exact installed artifact in a separate sanitized Windows job and fails hard on native loader/procedure/entry-point errors.
32. PL-0352 through PL-0367 begin only after PL-0351 is green and execute in exact order.
33. Every completed child publishes implementation/evidence and distinct GitHub-visible child log.
34. Owner handoffs/logs use clickable GitHub HTTPS links for prompts/criteria/commits/runs/artifacts; local C:\ paths are not accepted as handoff references.
35. OWNER DEV never regresses to Desktop LNK/PowerShell.
36. No private-data/secrets/signing leakage, tag/GitHub Release/V0.1 publication, M17 or PL-0368 execution.
37. PL-0368 remains DEFERRED_POST_M17.
38. Real blocker stops truthfully at AWAITING_MILESTONE_AUDIT.
39. Successful pre-M17 batch ends BATCH_COMPLETED_PRE_M17_GATE + AWAITING_MILESTONE_AUDIT.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_DISK_HYGIENE_PL0350_V07_CONTINUATION_CODEX_PROMPT_V13.md
