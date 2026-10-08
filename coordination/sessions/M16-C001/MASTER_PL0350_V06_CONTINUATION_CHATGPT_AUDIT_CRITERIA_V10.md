# M16-C001-R07 - PL-0350 V06 Continuation Master Audit Criteria V10

All criteria mandatory.

1. Live TASKS authorizes R07; Codex does not edit root TASKS.
2. Owner Desktop native PackLab.exe remains accepted and is refreshed after each published child.
3. PL-0350 V06 replaces opaque OCP native provenance with a PackLab-controlled exact source/package strategy.
4. PL-0350 green requires zero unresolved files/components, zero missing notices/source packages, zero forbidden Qt modules, green frozen capability smoke and unsigned installer.
5. PL-0351 starts only after PL-0350 is green.
6. PL-0351 tests the exact downloaded/installed installer in a separate sanitized Windows job and fails hard on native loader/procedure/entry-point errors.
7. PL-0352 through PL-0367 begin only after PL-0351 is green and execute in exact order.
8. Every completed child publishes implementation/evidence and a distinct GitHub-visible child log.
9. Every child/master owner handoff uses clickable GitHub HTTPS links for prompts, criteria, commits, logs, Actions runs and artifacts; local C:\ paths are not accepted as handoff references.
10. Published logs use GitHub URLs for referenced repository files/runs/artifacts where applicable.
11. OWNER DEV never regresses to Desktop LNK/PowerShell.
12. No private-data/secrets/signing leakage, tag/GitHub Release/V0.1 publication, M17 or PL-0368 execution.
13. PL-0368 remains DEFERRED_POST_M17.
14. A real blocker stops truthfully at AWAITING_MILESTONE_AUDIT.
15. Successful pre-M17 batch ends BATCH_COMPLETED_PRE_M17_GATE + AWAITING_MILESTONE_AUDIT.

Independent audit must inspect actual source/package locks, controlled native build evidence, hosted artifacts, installer provenance and clean-installed artifact evidence.
