# CLAUDE_PEER_REVIEW - PR #24 hide engine consoles - V02

Reviewer: Claude Code peer reviewer subagent (did not write this change). This is not CHATGPT_AUDIT or CODEX_PEER_REVIEW.
Delta reviewed: c98a0fc0..f4973ce9 (origin/fix/hide-engine-consoles), read-only worktree.

## V01 findings
- MEDIUM-1 RESOLVED: blender_capability.py adds `_run_hidden` (subprocess.run with creationflags=NO_WINDOW) and makes it the default `runner`. Callers that inject their own runner are unaffected.
- MEDIUM-2 RESOLVED: the cad_export_manifest.py `git rev-parse` call now passes creationflags=NO_WINDOW.
- Remaining `runner=subprocess.run` defaults: blender_render.py:115 is overridden by MockupJob in Studio. blender_glb_export.py:87 is not used by Studio. Neither needs a change.
- LOW-2 (neural/VGGT/openssl/sam21, not loaded by Studio) is accepted as deferred.

## New LOW
- LOW-3: tests/core/test_subprocess_runner.py test_blender_probe_and_cad_commit_hide_console calls `_run_hidden` directly. It does not check that discover_blender's default runner is `_run_hidden`. It swallows all exceptions from resolve_packlab_commit and asserts `flags and all(...)` without requiring 2 entries, so a skipped git call would still pass. On POSIX it only checks for 0. This does not block.

## Tests (worktree f4973ce9, .venv python, offscreen)
test_subprocess_runner, test_blender_capability, test_cad_export_manifest, test_blender_render, studio test_engineering_export, test_labels_export_library: 54 passed, 2 skipped.
NOT_VERIFIED: no real pythonw desktop click-through; CI not inspected.

## Verdict
PASS (code). The real-app check that no console flashes remains NOT_VERIFIED.
