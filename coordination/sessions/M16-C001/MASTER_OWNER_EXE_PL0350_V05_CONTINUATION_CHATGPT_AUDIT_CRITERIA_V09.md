# M16-C001-R06 - OWNER DESKTOP EXE + PL-0350 V05 Continuation Audit Criteria V09

All criteria mandatory.

## Owner Desktop EXE

1. Desktop owner entry point is a real `PackLab.exe`, not a `.lnk`.
2. Desktop owner-created `PackLab.lnk` is absent after successful EXE deployment.
3. Launcher EXE is a Windows GUI subsystem executable and does not open/leave a console.
4. Canonical PackLab ICO SHA-256 is `a4a655fc92796413130633703602885671f5b1a0773d045ebc79d6bd522c7fc1` and is embedded in the launcher EXE.
5. Windows Shell icon extraction from actual Desktop `PackLab.exe` is nonzero.
6. Native launcher contains no Qt/OCP/Open3D application payload; it launches the stable OWNER DEV runtime.
7. Native launcher does not invoke PowerShell as an intermediate launcher.
8. Launcher executes runtime `pythonw.exe` with a stable Python bootstrap.
9. Launcher verifies manifest/runtime/bootstrap and monitors child startup for at least 10 seconds.
10. Early child exit produces local diagnostic + native error dialog + nonzero launcher result.
11. Post-Codex refresh deterministically refreshes runtime, canonical icon, native launcher and Desktop EXE.
12. Start Menu entry targets the native launcher EXE, not PowerShell.
13. Actual Desktop `PackLab.exe` Shell-open launch is correlated to the observed PackLab process/window.
14. PackLab Studio remains alive and visible for at least 30 continuous seconds.
15. No PowerShell/console window is left visible.
16. Running PackLab window has nonzero icon handle.
17. Final validation leaves exactly one PackLab Studio window open for owner inspection; Codex does not close it before handoff.
18. Focused negative tests cover missing runtime/bootstrap, early exit, paths with spaces, embedded icon/GUI subsystem, Desktop EXE deployment and stale LNK removal.

## PL-0350 / continuation

19. Existing PL-0350 V05 native evidence gates are not weakened by the owner-local launcher work.
20. PL-0350 green still requires zero unresolved shipped files/components, zero missing notices/source packages, zero forbidden Qt components, frozen capability smoke green, and unsigned installer artifact.
21. PL-0351 starts only after PL-0350 is builder-green and tests the exact installed artifact in a separate sanitized Windows job.
22. PL-0352 through PL-0367 execute in exact order only after PL-0351 passes.
23. No tag/GitHub Release/V0.1/signing claim, M17 implementation or PL-0368 execution.
24. Owner Desktop EXE must remain working even if PL-0350 remains blocked.
25. Master handoff ends exactly `AWAITING_MILESTONE_AUDIT`.
