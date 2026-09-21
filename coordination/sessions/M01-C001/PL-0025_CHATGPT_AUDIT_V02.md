# PL-0025 — ChatGPT Independent Re-Audit V02

Decision: **CHANGES_REQUIRED**

Reason for re-audit: later M01 dependency/bootstrap work materially changes the task-runner integration state.

Repository: https://github.com/Sekiph82/PackLab
V01 audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CHATGPT_AUDIT_V01.md
Original criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CHATGPT_AUDIT_CRITERIA_V01.md

## New blocking evidence

PL-0029 now provides scripts/bootstrap_windows.ps1 and installs the locked dev tools into uv's project environment. The bootstrap does not activate that environment in the parent shell.

Current tools/tasks.py remains stale relative to that later authorized foundation:
- bootstrap detects that the script exists but still returns a deferred/explicit-invocation message instead of dispatching it;
- test runs the caller's sys.executable -m pytest rather than the locked uv environment;
- lint/type-check search global PATH for ruff/mypy rather than using the locked project environment.

Therefore the promised single documented entry point does not reliably orchestrate the now-implemented M01 developer toolchain after a clean bootstrap.

## Updated criterion disposition

1-7: PASS
8: **FAIL** — the root runner no longer provides a working single entry point for the now-implemented bootstrap/test/quality commands.
9: PASS
10: **FAIL** — commands that are now implemented in M01 are still treated as deferred/unavailable or rely on unrelated global environment state.
11-19: PASS
20: **FAIL** — a material cross-child task-runner integration defect remains.

Updated result: **17 / 20 PASS, 3 FAIL**

## Required remediation

Update tools/tasks.py so the current M01 command surface deterministically orchestrates the committed toolchain:
- bootstrap dispatches the committed Windows bootstrap safely on Windows and reports a clear unsupported/deferred state on other platforms until their bootstrap exists;
- test, lint and type-check run through the locked uv project environment without requiring shell activation or globally installed tools;
- diagnostics remains direct and safe;
- build remains explicitly deferred until its owning milestone;
- all subprocesses use argument arrays and shell=False.

Add focused task-runner tests for command construction, exit propagation, missing uv/platform cases and no global-PATH dependence.

Prior V01 audit remains historical evidence but is superseded by this V02 re-audit because later milestone evidence invalidated the final integration state.

Decision: **CHANGES_REQUIRED**
