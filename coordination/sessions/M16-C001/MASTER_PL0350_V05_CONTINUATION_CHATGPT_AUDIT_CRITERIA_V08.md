# M16-C001-R06 - OWNER DEV Repair + PL-0350 V05 Continuation Master Audit Criteria V08

All criteria mandatory.

## Phase 0 - integrated OWNER DEV repair

1. No separate owner-dev task/tracker/milestone is opened; repair occurs inside the current R06 execution.
2. Stable canonical shortcut icon exists at `%LOCALAPPDATA%\PackLab\OwnerDev\branding\PackLab.ico` with SHA-256 `a4a655fc92796413130633703602885671f5b1a0773d045ebc79d6bd522c7fc1`.
3. Desktop and Start Menu PackLab shortcuts point `IconLocation` to the stable branding ICO, not `OwnerDev\current`.
4. Shortcut/icon refresh is non-destructive and does not restart Explorer or mutate icon-cache/Taskband registry databases.
5. Launcher monitors spawned `pythonw.exe` for at least 8 seconds and fails on early exit with local diagnostic evidence.
6. OWNER DEV startup failure logging preserves local-only exception type/message/traceback plus deployed SHA/version context.
7. Actual Desktop `PackLab.lnk` is launched via Windows Shell `open` and the PackLab Studio window remains alive/visible for at least 15 continuous seconds before controlled cleanup.
8. The running window has a nonzero PackLab icon handle and both shortcuts resolve to the stable canonical icon path/hash.
9. `OWNER_DEV_READY` is emitted only after runtime/shortcut/icon/manifest checks pass.
10. PL-0350 work does not begin until the real Desktop launcher acceptance passes.

## PL-0350 V05 and continuation

11. PL-0347 V02 through PL-0349 V03 remain independently accepted.
12. PL-0350 V05 closes the final five native component gates with exact file maps and verified source evidence.
13. No component status is cleared by blanket registry edit while any owned staged row remains unresolved.
14. PL-0350 green requires zero unresolved shipped files/components, zero missing notices/source packages, zero forbidden Qt components, green frozen capability smoke and unsigned installer artifact.
15. PL-0351 starts only after PL-0350 V05 is builder-green.
16. PL-0351 downloads and installs the exact installer in a separate sanitized Windows job and hard-fails native loader/procedure/entry-point errors.
17. PL-0352 through PL-0367 begin only after PL-0351 is green and execute in exact order.
18. Every completed child has distinct implementation/evidence and required child-log publication ending `READY_FOR_INDEPENDENT_AUDIT`.
19. No private-data/secrets/signing leakage, tag/GitHub Release/V0.1 publication, M17 implementation or PL-0368 execution.
20. PL-0368 remains `DEFERRED_POST_M17`.
21. Successful batch ends `BATCH_COMPLETED_PRE_M17_GATE` + `AWAITING_MILESTONE_AUDIT`; real blockers stop truthfully.

Independent audit must inspect the repaired real Desktop shortcut behavior, stable icon path/hash, early-exit diagnostics, actual native maps/source hashes, hosted compliance artifacts, installer provenance and separate clean-install evidence.
