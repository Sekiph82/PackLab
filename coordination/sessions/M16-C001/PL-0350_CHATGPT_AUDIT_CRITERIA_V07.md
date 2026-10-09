# PL-0350 - ChatGPT Audit Criteria V07

Task: **Dedicated controlled-runtime producer + verified cache + packaging continuation**

All criteria mandatory.

1. Live TASKS, partial audit V09 and V06 audit are read; Codex does not edit root TASKS.
2. Owner Desktop PackLab.exe remains working and is not conflated with installer portability.
3. Windows workflow separates controlled OCP runtime production from PackLab packaging into distinct jobs.
4. OCP CMake receives explicit `N_PROC=4`; hosted evidence records worker count.
5. Controlled runtime producer creates a sealed bundle containing OCP runtime + manifest + source evidence + metadata, without build-tree/source-archive leakage.
6. Cache key is derived from exact native build inputs/contracts and is independent of unrelated PackLab commit changes.
7. No broad fallback restore key may accept a runtime from different native inputs.
8. Every cache hit is independently validated against current source-lock/build-contract digests and every runtime file hash.
9. Invalid/stale cache is rejected and triggers exact rebuild.
10. Job 1 executes bounded OCP smoke even on cache hit.
11. Job 1 publishes the validated bundle as a same-run short-lived artifact.
12. Job 2 downloads that exact artifact and does not directly consume cross-run cache.
13. Job 2 never invokes the controlled OCP source builder.
14. Controlled runtime install removes opaque wheel runtime/libs and fails if they survive.
15. Fresh packaged Qt GUI/QtPdf/OCP/Open3D no-network smoke passes.
16. Controlled OCP manifest validates bidirectionally against the staged product.
17. Redistribution gate reaches zero unresolved files/components/missing notices/source packages/forbidden Qt modules.
18. Engineering status is `CLEARED_FOR_PL0350_ENGINEERING_PACKAGING`, with legal review required and public release unauthorized.
19. Unsigned installer is built only after clearance and final exact-input validation.
20. First cache-miss run completes producer job within hosted job limit and records timing evidence.
21. A second run/rerun proves a verified cache HIT and no pywrap rebuild.
22. Quality/focused/full pytest/mypy/Ruff/compile/privacy checks pass.
23. No tag/GitHub Release/V0.1/signing claim, PL-0351+, M17 or PL-0368 occurs inside this child.
24. OWNER DEV native EXE refresh remains green.
25. Implementation/evidence and V07 log are distinct.
26. Owner handoff and published logs use GitHub HTTPS links for commits/logs/runs/artifacts/prompt/criteria.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V07.md
