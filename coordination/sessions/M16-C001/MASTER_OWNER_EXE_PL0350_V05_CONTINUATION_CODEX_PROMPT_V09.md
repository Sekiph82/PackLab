# M16-C001-R06 - OWNER DESKTOP EXE + PL-0350 V05 + PL-0351→PL-0367 Continuation Master V09

Milestone: **M16 - CI/CD, Signing & Distribution**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

This V09 supersedes the OWNER DEV launcher/shortcut portions of Master V08 while preserving the PL-0350 V05 native-evidence work and downstream continuation rules.

Current owner decision:

> The Desktop entry point must be a real `PackLab.exe`, not a `.lnk`.
> The owner will double-click the EXE directly.
> No PowerShell/terminal flash is acceptable.
> The canonical PackLab icon must be embedded in the EXE.
> The final validation window must remain open for owner inspection at handoff.

PL-0350 V05 prompt/criteria remain authoritative for the native redistribution/source-evidence portion after Phase 0:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V05.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V05.md

PL-0351 amended clean-install prompt/criteria:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CHATGPT_AUDIT_CRITERIA_V01.md

## Start rule

1. Synchronize the managed Codex checkout non-destructively with latest `origin/main`.
2. Preserve owner-local Desktop work except the obsolete PackLab owner-launcher files explicitly replaced by this task.
3. Read live root `TASKS.md`; it must authorize this V09 continuation.
4. Read V05 redistribution prompt/criteria and the latest V05 Codex/evidence logs.
5. Do not edit root `TASKS.md`.
6. Do not start M17 or PL-0368.

# Phase 0 - Replace Desktop .lnk with a real PackLab.exe

This is an integrated owner-local delivery fix inside the current R06 execution. Do not create a separate milestone/task/tracker.

## 0.1 Required architecture

Do **not** package the whole PackLab application into this owner-local Desktop EXE.

PL-0350 redistribution remains blocked. Therefore the immediate Desktop EXE must be a tiny owner-local native Windows GUI launcher which contains no Qt/OCP/Open3D application payload.

The EXE launches the existing stable owner runtime:

`%LOCALAPPDATA%\PackLab\OwnerDev\current`

The runtime remains refreshed from exact published Git HEAD via the existing locked OWNER DEV mechanism.

Required stable paths:

- source/runtime:
  `%LOCALAPPDATA%\PackLab\OwnerDev\current`
- stable launcher:
  `%LOCALAPPDATA%\PackLab\OwnerDev\launcher\PackLab.exe`
- canonical icon:
  `%LOCALAPPDATA%\PackLab\OwnerDev\branding\PackLab.ico`
- owner logs:
  `%LOCALAPPDATA%\PackLab\OwnerDev\logs`
- actual Desktop executable:
  `<real Windows Desktop known folder>\PackLab.exe`

The Desktop `PackLab.exe` may be a byte-identical copy of the stable launcher EXE.

## 0.2 Native GUI launcher implementation

Add a checked-in launcher source under `tools/dev/`, for example:

`tools/dev/PackLabOwnerLauncher.cs`

and a checked-in deterministic build/deploy script, for example:

`tools/dev/build_owner_packlab_exe.ps1`.

Preferred implementation is a minimal Windows GUI executable built locally using a Windows-provided or already-installed compiler toolchain. Do not download a compiler/runtime at launch time.

The launcher must be compiled as **Windows GUI / WinExe**, not console.

### Toolchain

Prefer, in this order if present:

1. installed Visual Studio / Build Tools C# compiler;
2. Windows .NET Framework compiler under `%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe`;
3. existing installed `dotnet` SDK with a framework-dependent Windows GUI target.

Do not install/download a new toolchain automatically.

If none is available, stop with exact evidence instead of falling back to a PowerShell shortcut.

## 0.3 Embedded canonical icon

Compile the launcher with the exact canonical icon embedded as the executable icon.

Canonical ICO SHA-256:

`a4a655fc92796413130633703602885671f5b1a0773d045ebc79d6bd522c7fc1`

Use the canonical repository branding asset and verify bytes before compilation.

After build, verify:

- stable launcher EXE exists;
- Desktop PackLab.exe exists;
- EXE has a non-empty embedded icon;
- Windows Shell icon extraction from Desktop PackLab.exe returns a nonzero icon handle;
- Desktop EXE visually resolves to the PackLab icon source, with no `.lnk` IconLocation dependency;
- PE is GUI subsystem, not console subsystem.

Do not claim success merely because the ICO source file exists.

## 0.4 Remove obsolete Desktop shortcut

After and only after the real Desktop EXE is built and verified:

- remove the obsolete owner-created Desktop `PackLab.lnk`;
- do not remove unrelated owner files;
- ensure exactly one PackLab owner launcher remains on Desktop: `PackLab.exe`.

Start Menu may use either:

- a shortcut targeting the stable native `%LOCALAPPDATA%\PackLab\OwnerDev\launcher\PackLab.exe`, or
- a copied launcher EXE if technically appropriate.

It must no longer target PowerShell or `launch_owner_packlab.ps1`.

Taskbar pinning, when available, should originate from the native launcher/PackLab identity, never the old PowerShell shortcut.

## 0.5 Python bootstrap must not depend on PowerShell

The native launcher must start the owner runtime directly.

Do not invoke `powershell.exe` as an intermediate launcher.

Create a stable Python bootstrap script inside the owner runtime, for example:

`tools/dev/owner_packlab_bootstrap.py`

which:

- computes runtime root from `LOCALAPPDATA`;
- inserts the runtime `core/src` and `apps/windows-studio/src` paths;
- runs `packlab_studio` as the real module;
- preserves OWNER DEV diagnostic environment.

The native EXE should execute:

`current\.venv\Scripts\pythonw.exe <bootstrap.py>`

with no console.

## 0.6 Native launcher diagnostics

The native EXE must:

1. verify the owner runtime manifest exists;
2. verify `pythonw.exe` exists;
3. verify the bootstrap script exists;
4. read the deployed Git SHA/version from the manifest;
5. set OWNER DEV diagnostic environment variables for the child;
6. launch child with no console;
7. monitor child for at least **10 seconds**;
8. if the child exits during the stability window:
   - capture exit code;
   - write a timestamped owner-local log;
   - include deployed SHA/version;
   - include the Python startup log if present;
   - show a native Windows error dialog;
   - exit nonzero;
9. if child remains alive, launcher may exit success.

The EXE itself must not leave a terminal window.

## 0.7 Post-Codex refresh behavior

Update the standing owner refresh so that after every published Codex implementation:

1. owner runtime is refreshed from exact published HEAD;
2. stable canonical ICO is verified;
3. native owner launcher EXE is built/rebuilt deterministically if source/icon changed or missing;
4. stable launcher EXE is verified;
5. Desktop `PackLab.exe` is refreshed atomically from the stable launcher;
6. obsolete Desktop `PackLab.lnk` is absent;
7. Start Menu entry targets the native EXE, not PowerShell;
8. manifest/deployed SHA checks pass;
9. output includes:
   `OWNER_DEV_EXE_READY <full_sha> <desktop_exe> <launcher_exe>`

Do not print the old `OWNER_DEV_READY` success line unless it also guarantees the native EXE contract.

## 0.8 Mandatory actual Desktop acceptance

This acceptance is stronger than prior shortcut tests.

After publishing the Phase 0 implementation and refreshing the owner runtime:

1. locate the actual current Windows Desktop known folder;
2. prove `PackLab.exe` exists there;
3. prove `PackLab.lnk` does **not** exist there;
4. inspect the actual Desktop EXE's PE subsystem and embedded icon;
5. invoke the **actual Desktop `PackLab.exe`** using Windows Shell `open`;
6. verify the visible top-level window title is `PackLab Studio`;
7. verify the running PackLab window icon handle is nonzero;
8. verify the child PackLab process remains alive and the window remains visible for at least **30 continuous seconds**;
9. verify no PowerShell/console window is left visible;
10. verify no owner-startup error log was produced for this successful launch;
11. **DO NOT CLOSE THE PACKLAB WINDOW AFTER THIS FINAL ACCEPTANCE. Leave exactly one PackLab Studio window open for the owner to inspect manually after Codex handoff.**

If the app exits before 30 seconds, Phase 0 FAILS. Inspect the local diagnostic and repair the actual cause before continuing.

Do not fake acceptance by:

- launching a different worktree/runtime;
- launching Python directly instead of Desktop PackLab.exe;
- detecting a window from another PackLab process;
- immediately closing the window after detecting it;
- validating only the source ICO.

Record PID/process start time and correlate it to the Desktop EXE launch chain.

## 0.9 Tests

Add focused tests for:

- launcher source/build contract;
- GUI subsystem and embedded icon;
- missing runtime/manifest/bootstrap failures;
- early child exit;
- path with spaces;
- Desktop EXE deployment;
- stale Desktop LNK removal;
- Start Menu no-PowerShell target;
- post-Codex refresh EXE contract.

The actual owner-machine 30-second visible acceptance remains mandatory in addition to tests.

# Phase 1 - PL-0350 V05 native redistribution/source evidence

Only after Phase 0 passes, resume the existing PL-0350 V05 work.

Do not weaken the existing five native-component/source-evidence gates.

If PL-0350 remains blocked:

- publish exact evidence and V05 log;
- preserve the working Desktop PackLab.exe;
- update master log;
- stop at `AWAITING_MILESTONE_AUDIT`.

If PL-0350 becomes builder-green, continue automatically to PL-0351.

# Phase 2 - PL-0351 clean installed-artifact portability

Execute the amended PL-0351 exactly.

This remains the production/distribution test for the prior QtCore `The specified procedure could not be found` failure.

The owner-local Desktop launcher EXE is **not** evidence that the future packaged installer passes PL-0351.

If PL-0351 is green, continue PL-0352 through PL-0367 in exact existing order.

# Phase 3 - PL-0352 through PL-0367

Continue the existing authorized children in order only while every hard gate is green.

PL-0368 remains `DEFERRED_POST_M17`.

# Validation / publication

Publish implementation/evidence commits, then update/create the R06 master log V09.

Record:

- compiler/toolchain actually used;
- launcher source path;
- stable launcher EXE SHA-256/bytes;
- Desktop EXE SHA-256/bytes;
- canonical ICO SHA;
- PE GUI subsystem proof;
- embedded icon extraction proof;
- obsolete Desktop LNK absence;
- Start Menu target;
- exact Desktop EXE launch PID chain;
- 30-second visible/alive result;
- no-console result;
- final left-open PackLab window PID;
- owner runtime deployed SHA;
- PL-0350 continuation result;
- final parity.

If Phase 0 succeeds but PL-0350 remains blocked, the owner must still retain a working Desktop `PackLab.exe`.

End the master handoff exactly:

`AWAITING_MILESTONE_AUDIT`
