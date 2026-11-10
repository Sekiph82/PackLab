# PL-0376 — Codex Prompt V01

Task: **Cover glossy PET failure behavior**  
Milestone: **M17** · Cycle: **M17-C001**

Add regression tests using the glossy PET benchmark samples. Exercise specular/high-gloss quality diagnostics and ensure missing reliable texture/geometry evidence is surfaced instead of silently treated as a successful reconstruction. Keep the test and expected values synthetic/nonphysical. Add tests only unless inspection identifies a missing required production behavior; report that gap before changing runtime behavior. Do not run tests until the M17 milestone-end batch. Write `PL-0376_CODEX_LOG_V01.md`.
