# CLAUDE_PEER_REVIEW — PR #12 Studio Build model (V01)

- Reviewer: Claude Code independent peer reviewer (not the builder; did not edit source)
- Scope: PL-0443, PL-0453, PL-0454, PL-0455, PL-0457
- Branch/head: `origin/feat/studio-build-model` @ `fb49f86a`, diffed against `origin/main` (10 files, +1775/-59)
- Verdict: **PASS_WITH_NOTES** (no HIGH findings)

## What I verified myself
- CI: `gh run view 44809392785` returns PackLab Windows Python Quality, headSha fb49f86a, conclusion success.
- Focused tests in a detached worktree at fb49f86a: `tests/studio/test_build_model.py` plus `test_project_menus.py` gave **13 passed**.
- I re-ran the implementer's `studio_e2e_menus.py` (offscreen) on fb49f86a. It reproduced the logged output: File/Help menus, default project "My scans", Engines rows, diagnostic bundle written, preferences saved.
- My own probe tests (scratch, deleted): (a) restarting with auto-build **ON** and calling `refresh_inbox()` queues no build, so startup does not rebuild; (b) two builds can run **concurrently** (confirmed 2 RUNNING).
- Implementer evidence: I inspected `studio-e2e-build.log` and screenshots 12/13. Log shows 8 stages, 24/28 registered, 419 s, 193,761 points. Engines came from `C:\Users\sekip\Tools` (env/explicit), not the PL-0444 bundle.
- Thread safety: worker-thread JobManager calls go through `MainThreadInvoker` (BlockingQueuedConnection, build_model.py:100-133). Single writer, sound.
- Cancel: `run_reconstruction_stage` -> `subprocess_runner.run_process` with CREATE_NEW_PROCESS_GROUP + `taskkill /T /F` (core/src/packlab_core/subprocess_runner.py:33-36,108). The process tree is killed. Both the cancel-while-queued and the cancel-while-running paths are tested.
- Raw copy (build_model.py:549-567): digest regex, source re-hash, staging plus `os.replace`, idempotent when the target hash matches.
- Authority: the test asserts manifest `authority_class == RECONSTRUCTION_OBSERVATION` and `scale_state == relative`. NEXT_STEPS text states "not Scan Master".
- Diagnostic bundle: existing `diagnostics.redact` applies. The generated bundle contains no username or paths.
- FFmpeg: discovered at run time only and not bundled. The register row says so (MEDIUM ATTENTION). The local ffmpeg is gyan 9.0.1 "full" (GPL).

## HIGH
None.

## MEDIUM
1. **Probe baseline vs. the command plan disagree.** In `navigation.py:149-176` / `engine_probe`, the baseline is COLMAP 3.12.6, so the bundled/used COLMAP 4.2.1 shows as "(unsupported)" in Settings > Engines. Meanwhile the plan in `build_model.py:325,347` uses 4.x option names (`FeatureExtraction.use_gpu`, `FeatureMatching.use_gpu`). The panel therefore misleads the owner about the one version that is known to work. Fix: update `COLMAP_BASELINE` to 4.2.1 or add a supported range, then follow up.
2. **Untrusted HEIC is passed to ffmpeg with auto-probed format** (`build_model.py:293-303`). Content-sniffing lets a crafted ".heic" (for example an HLS/concat playlist) make ffmpeg open other local files or URLs. Add `-protocol_whitelist file` and force the demuxer (`-f mov`). Also, the ffmpeg binary is not in `BackendProvenance.executable_sha256` (build_model.py:233-239), so the decode tool is not traceable.

## LOW
3. No build queue or dedupe. `shell.py:328` / `build_model.py:589-622` start a thread per request, so repeated clicks or several imports run COLMAP builds in parallel. The view's "Queued" label is optimistic.
4. `capture_inbox.py:139-140` fails open: if `entries()` throws at session creation, every already-imported scan later auto-builds.
5. `build_model.py:290` uses the HEIC target `stem + ".jpg"`, so `IMG_1.HEIC` and `IMG_1.JPG` collide silently.
6. `shutil.which("ffmpeg")` (build_model.py:214) also searches the current directory on Windows. `navigation.py:139` runs the probe synchronously on the UI thread with a 5 s timeout per engine.
7. Test gap: in `tests/studio/test_build_model.py:284` the "never auto-build at startup" assert runs with auto-build **OFF**, so it passes trivially. My probe shows the behavior is correct with auto-build ON. No test covers the real ffmpeg/COLMAP argument content.
8. Viewer initial view (screenshot 13): the model is small and rotated, because the COLMAP frame is arbitrary. Not misleading: there is a Fit button, the status says "Units as stored in the file", and the scale is relative. Cosmetic.
9. PL-0453 lists the next steps as scale/measure and labels. Those appear only as text, while buttons exist for cleanup, Design Model and Export.

## Acceptance note
The real-window evidence is offscreen-rendered Qt captures from the real PackLab window with real engines (COLMAP 4.2.1 / OpenMVS 2.4.0). PL-0443's "from the window" evidence used owner-installed engines, not the bundle. MEDIUM 1 and 2 can be tracked as follow-ups and do not block.
