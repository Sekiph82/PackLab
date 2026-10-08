# M16-C001-R07 - OWNER DESKTOP EXE STARTUP REPAIR + PL-0350 V06 Continuation Audit Criteria V11

All criteria mandatory.

## Phase 0 - Owner Desktop EXE startup repair

1. No separate task/milestone/tracker is opened; the repair occurs at the beginning of the current R07 master.
2. Codex reads the newest real owner-local `%LOCALAPPDATA%\PackLab\OwnerDev\logs\startup-*.log` produced by the failing Desktop EXE before changing code.
3. The exact deployed SHA/version/failure category/child exit or Python exception details are correlated to the failing Desktop EXE launch.
4. The failure is reproduced using the **actual Desktop `PackLab.exe`**, not Python/source/worktree shortcuts.
5. The root cause is fixed rather than hidden by timeout increases or error suppression.
6. Runtime manifest, copied runtime source, locked `.venv` environment and Desktop launcher all bind to the same published GitHub HEAD.
7. Post-Codex refresh truthfully updates the runtime and dependencies before promotion.
8. Final acceptance starts with no unrelated PackLab window that could produce a false positive.
9. Actual Desktop `PackLab.exe` is Shell-opened and its launcher → pythonw → visible PackLab Studio process chain is correlated.
10. PackLab Studio remains alive, visible and responsive for at least **60 continuous seconds**.
11. The successful 60-second run creates no new startup-error log.
12. No PowerShell/console window remains.
13. Embedded PackLab icon remains valid.
14. Deployed runtime SHA equals current published GitHub main.
15. Exactly one working PackLab Studio window is left open for owner inspection at handoff.
16. Source-mode smoke, temporary process lifetime or launcher exit code alone cannot satisfy acceptance.
17. Local startup logs remain private; GitHub logs summarize safe root-cause evidence without publishing sensitive local details.
18. Owner-facing handoff references use GitHub HTTPS links, never local C:\ paths.

## PL-0350 V06 and continuation

19. PL-0350 V06 starts only after Phase 0 passes.
20. PL-0350 V06 replaces opaque OCP native provenance with a PackLab-controlled exact source/package strategy.
21. PL-0350 green requires zero unresolved files/components, zero missing notices/source packages, zero forbidden Qt modules, green frozen capability smoke and unsigned installer.
22. PL-0351 starts only after PL-0350 is green and tests the exact installed artifact in a separate sanitized Windows job.
23. PL-0352 through PL-0367 execute in exact order only after PL-0351 passes.
24. Every completed child publishes implementation/evidence and a distinct GitHub-visible child log.
25. Every child/master owner handoff uses clickable GitHub HTTPS links for prompts, criteria, commits, logs, Actions runs and artifacts.
26. OWNER DEV never regresses to Desktop LNK/PowerShell.
27. No private-data/secrets/signing leakage, tag/GitHub Release/V0.1 publication, M17 or PL-0368 execution.
28. PL-0368 remains DEFERRED_POST_M17.
29. Real blockers stop truthfully at AWAITING_MILESTONE_AUDIT.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_OWNER_EXE_REPAIR_PL0350_V06_CONTINUATION_CODEX_PROMPT_V11.md
