# M16-C001-R07 Owner Desktop EXE Startup Repair Evidence

Status: implementation and owner-runtime acceptance evidence; independent audit pending.

## Scope and source authority

- Target: the real Windows Desktop known-folder `PackLab.exe` that the owner double-clicks.
- Master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_OWNER_EXE_REPAIR_PL0350_V06_CONTINUATION_CODEX_PROMPT_V11.md
- Master audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_OWNER_EXE_REPAIR_PL0350_V06_CONTINUATION_CHATGPT_AUDIT_CRITERIA_V11.md
- The owner-local startup logs remain private and are not committed.

## Observed failure and diagnosis

The newest owner-local failure log created by the real Desktop executable recorded `reason=launcher_failure`, `System.IO.FileNotFoundException`, and `exception_message=Owner runtime manifest is missing.` It reported `deployed_sha=unknown` and `studio_version=unknown`, consistent with failure before a runtime manifest could be read. The machine-specific log, timestamp, and filesystem path are intentionally omitted here.

The launcher was failing closed when the runtime manifest was absent during refresh. The repair now prepares an immutable, source-identified release runtime (including the locked environment and manifest), builds the native launcher with the exact source commit and runtime ID embedded, and publishes the Desktop executable only after that release is prepared. The native launcher resolves its runtime from that immutable release. A separate physical compatibility copy at `OwnerDev\\current` is prepared for tools that consume the compatibility path; it is not the launcher's runtime source. Manifest validation binds the launcher, source commit, runtime ID, locked `uv.lock` digest, and successful dependency smoke result.

Implementation commits:

- https://github.com/Sekiph82/PackLab/commit/a10ab5f15e942569572d38f657060afb317d620a
- https://github.com/Sekiph82/PackLab/commit/5b2a7dfc375a3577ad9a06188d9c00484b0db9d6
- https://github.com/Sekiph82/PackLab/commit/95b2fd8f590794926869ad241800673c24867d29
- https://github.com/Sekiph82/PackLab/commit/e56db18ce9e502408499c7a3461b61e10f67fed4
- https://github.com/Sekiph82/PackLab/commit/3f116d80fcffd79d83a67e08bfee64c205b420f0

The intermediate refresh attempts exposed identity parsing and compatibility-path access failures; those were corrected before the successful gate. Junction-based compatibility paths were replaced with a staged physical copy because the real AppData read test did not reliably traverse them.

## Actual Desktop EXE acceptance

After refreshing from published `origin/main` at `3f116d80fcffd79d83a67e08bfee64c205b420f0`, the real Desktop `PackLab.exe` was Shell-opened with no pre-existing PackLab Studio window. The observed process chain was the native launcher, the immutable release `.venv` `pythonw.exe`, and the visible Studio process. Exactly one visible window titled `PackLab Studio` remained open.

- Continuous visible/alive interval: 60.1 seconds.
- Qt responsiveness: 58 successful benign `WM_NULL` responsiveness checks during the interval.
- Startup error log: no new log was created for the successful launch.
- Console/PowerShell child: none remained.
- Runtime source commit, manifest source commit, launcher-embedded source commit, and current published `main`: `3f116d80fcffd79d83a67e08bfee64c205b420f0`.
- The launcher verified the immutable runtime manifest and exact `uv.lock` digest before starting the child runtime.
- Embedded Desktop EXE icon was present and valid.

This acceptance is implementer evidence only; independent audit remains pending. This evidence commit itself must be followed by the standing OWNER DEV refresh and a fresh 60-second check against its resulting published commit.

