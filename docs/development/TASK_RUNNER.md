# PackLab task runner

`python tools/tasks.py <command>` is the cross-platform entry point for common M01 developer actions. Test, lint, type-check, and diagnostics commands are executed as explicit `uv run --locked ...` argument arrays, without shell activation or global pytest/Ruff/mypy lookup. Windows bootstrap is dispatched as an explicit PowerShell argument array. The runner returns child exit codes and never edits the live tracker. It orchestrates owned tools; it is not a second task ledger or a source of domain truth.

## Commands

| Command | Current behavior |
| --- | --- |
| `help` / `list` | List supported commands |
| `diagnostics` | Run the redacted environment report through `uv run --locked` |
| `test` | Run pytest through `uv run --locked` and the project dev group |
| `lint` | Run Ruff through `uv run --locked` and the project dev group |
| `type-check` | Run mypy through `uv run --locked` and the project dev group |
| `bootstrap` | Dispatch `scripts/bootstrap_windows.ps1` on Windows; defer with nonzero status elsewhere |
| `build` | Report deferred platform build work; it does not pretend to build |

Examples:

```powershell
python tools/tasks.py help
python tools/tasks.py diagnostics
python tools/tasks.py test
```

The runner does not install dependencies itself, select an external engine, mutate system settings, invoke a shell command string, or replace `TASKS.md`. `uv run --locked` may use the already-declared project environment but refuses lockfile drift. Tool versions, dependency locking, quality configuration, and platform builds remain owned by their separate M01 tasks or later milestones. Build remains an explicit deferred nonzero command until its owning milestone.
