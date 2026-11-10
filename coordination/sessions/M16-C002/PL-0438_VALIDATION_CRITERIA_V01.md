# PL-0438 Local Validation Criteria V01

Use these checks to assess the Codex implementation. This is not an independent audit or owner acceptance artifact.

## Queue validator

- Reads only the supplied PackLab root `TASKS.md` and remains read-only.
- Uses the explicit current task and status fields; does not infer queue authority from checkbox order.
- Accepts canonical PackLab PL IDs and dotted identifiers where present, while preserving exact identity/title matching.
- Rejects malformed/duplicate IDs, current-task/title mismatch, status-marker mismatch, multiple in-progress rows, and foreign repository/branch authority.
- Prints a stable machine-readable JSON result on request and exits nonzero on invalid state.

## Governance and scope

- Root `TASKS.md` remains the only live task-status tracker.
- PackLab's active owner delegation supersedes contradictory historical workflow clauses without rewriting historical audit evidence.
- Sequencing-only wait/stop text does not prevent autonomous progress; genuine decision, safety, legal, security, licensing, environment, authority, or resource blockers remain explicit.
- No files outside PackLab are modified. No shared dashboard source, private Codex database, `.hiveai`, or AppData task store is read or changed.
- No GitHub Actions, paid CI, PR, native build, or public/factory release is triggered or claimed.
- PL-0354 remains open until actual supported macOS/Xcode execution of all 205 XCTest cases.

## Commands

```powershell
python -m pytest -q tests/ci/test_codex_task_queue.py
python tools/codex/task_queue.py --task PL-0438 --json
git status --short
git diff --check
```

All commands are local. A successful result is implementation evidence only.
