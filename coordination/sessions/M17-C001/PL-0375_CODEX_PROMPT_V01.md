# PL-0375 — Codex Prompt V01

Task: **Cover low-texture white HDPE failure behavior**  
Milestone: **M17** · Cycle: **M17-C001**

Add regression tests using the matte-white HDPE benchmark samples. Verify the current capture/reconstruction quality gates classify low texture as a limitation, warning, or blocked result instead of inventing confident surface detail or physical accuracy. Keep data synthetic and all ranges nonphysical. Do not change expected thresholds to make the scenario pass. Add tests only unless inspection identifies missing required production behavior; report that gap before changing runtime behavior. Defer all test execution to the M17 milestone-end batch. Write `PL-0375_CODEX_LOG_V01.md`.
