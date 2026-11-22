# CLAUDE_PEER_REVIEW - PR #24 hide engine consoles - V01

Reviewer: Claude Code peer reviewer subagent (did not write this change). This is not CHATGPT_AUDIT or CODEX_PEER_REVIEW.
Branch: origin/fix/hide-engine-consoles @ c98a0fc0 (1 commit on top of origin/main 185c2dbf). Diff: 6 files, +48/-3.
Inspected read-only in worktree C:\Users\sekip\Desktop\PackLab-wt-noconsole.

## What is correct
- `subprocess_runner.NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)`: 0 on POSIX, so `creationflags=0` is legal there; the POSIX Popen branch is unchanged (`start_new_session=True`).
- `CREATE_NEW_PROCESS_GROUP | NO_WINDOW` in run_process (Windows branch) is a valid combination. Cancellation uses `taskkill /PID <pid> /T /F`, which matches the process tree by PID, so a hidden console does not affect it. The taskkill call is now hidden too. Grandchildren inherit the hidden console, so they do not open new windows either.
- No import cycle: subprocess_runner imports only stdlib. capabilities, engine_probe, navigation and design_workbench import it one way only.
- navigation._probe_runner still falls back to the scratch `*.log` file when stdout is empty, so the OpenMVS banner is still read whether or not OpenMVS sees a console.
- COLMAP/OpenMVS/ffmpeg (HEIC decode and the `-version` probe) all go through run_reconstruction_stage -> run_process, so they are covered. The Blender mockup render goes through MockupJob's Popen, which is covered. The VGGT worker already used CREATE_NO_WINDOW.

## Findings
MEDIUM-1: core/src/packlab_core/blender_capability.py:59 `discover_blender(runner=subprocess.run)` has no flag. It is reached from the GUI through design_workbench.py:473 `find_blender()` -> `prepare_mockup` (:783). The probe runs `blender.exe --background` (Windows console subsystem) on every mockup prepare, so a console still flashes. Fix: pass a no-window runner or add the flag in the default probe.
MEDIUM-2: core/src/packlab_core/cad_export_manifest.py:248 `git rev-parse HEAD` has no flag. It is reached from Studio engineering export (STEP/STL/OBJ/GLB via engineering_export.py:360/367 -> build_cad_export_manifest -> resolve_packlab_commit). This happens in the non-frozen OwnerDev checkout when PACKLAB_COMMIT is unset. Result: a git console flashes on export.
LOW-1: The new test only checks that the CREATE_NO_WINDOW bit is set in run_process. It does not check that CREATE_NEW_PROCESS_GROUP is kept (a regression that dropped the group bit would still pass). No test covers the flag in capabilities, engine_probe, navigation._probe_runner, _build_revision or MockupJob.
LOW-2: There are still unflagged calls that the GUI does not reach today: neural_reconstruction_runtime.py:178/186, vggt_worker.py:180/191 (git check_output), transfer_security.py:59 (openssl; the Studio receiver uses the cryptography path ensure_receiver_tls_identity), and sam21_backend. None of these is imported by the studio modules (checked with a sys.modules check). Flag them if they become GUI-reachable.

## Tests run (reviewer, worktree, .venv python, QT_QPA_PLATFORM=offscreen)
- tests/core/test_subprocess_runner.py, test_engine_probe.py, test_capabilities.py: 30 passed.
- tests/studio/test_navigation.py, test_build_model.py, test_engineering_export.py, test_labels_export_library.py, tests/core/test_reconstruction_process.py, test_blender_capability.py, test_blender_render.py, test_cad_export_manifest.py: 63 passed, 2 skipped.
- New test test_windows_children_get_no_console_window: passed on Windows.
NOT_VERIFIED: no real pythonw click-through on the desktop to watch for console flashes. CI was not inspected.

## Verdict
CHANGES_REQUIRED (MEDIUM-1, MEDIUM-2: GUI-reachable console flashes still happen, which is the PR goal). The current diff is safe and correct; no regression was found.
