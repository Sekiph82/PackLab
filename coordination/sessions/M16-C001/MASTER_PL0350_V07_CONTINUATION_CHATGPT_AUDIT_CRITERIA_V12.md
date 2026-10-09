# M16-C001-R08 - PL-0350 V07 Continuation Master Audit Criteria V12

All criteria mandatory.

1. Live TASKS authorizes R08; Codex does not edit root TASKS.
2. Working native Desktop PackLab.exe remains healthy for owner use.
3. PL-0350 V07 uses a dedicated controlled-runtime producer job with explicit N_PROC=4 and a separate packaging job.
4. Controlled runtime cache key is based on exact native build inputs rather than ordinary PackLab commit identity.
5. Cache hit is fail-closed validated against source-lock/build-contract/file digests before use.
6. Same-run artifact transfer separates cache authority from packaging consumption.
7. Packaging job never rebuilds OCP/OCCT.
8. First cache-miss producer run finishes within hosted job limit.
9. Second run/rerun proves verified cache HIT without pywrap rebuild.
10. PL-0350 green requires zero unresolved shipped files/components, zero missing notices/source packages, zero forbidden Qt modules, green packaged capability smoke and unsigned installer.
11. PL-0351 starts only after PL-0350 V07 is green.
12. PL-0351 tests the exact installed artifact in a separate sanitized Windows job and fails hard on native loader/procedure/entry-point errors.
13. PL-0352 through PL-0367 begin only after PL-0351 is green and execute in exact order.
14. Every completed child publishes implementation/evidence and distinct GitHub-visible child log.
15. Owner handoffs/logs use clickable GitHub HTTPS links for prompts/criteria/commits/runs/artifacts; local C:\ paths are not accepted.
16. OWNER DEV never regresses to Desktop LNK/PowerShell.
17. No private-data/secrets/signing leakage, tag/GitHub Release/V0.1 publication, M17 or PL-0368 execution.
18. PL-0368 remains DEFERRED_POST_M17.
19. Real blocker stops truthfully at AWAITING_MILESTONE_AUDIT.
20. Successful pre-M17 batch ends BATCH_COMPLETED_PRE_M17_GATE + AWAITING_MILESTONE_AUDIT.

Independent audit must inspect exact cache key inputs, restored-bundle validation, cache-miss/cache-hit hosted evidence, redistribution artifacts, installer provenance and clean-installed artifact evidence.
