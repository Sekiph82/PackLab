# PackLab task runner

`python tools/tasks.py <command>` is the cross-platform entry point for common developer actions. It uses explicit subprocess argument arrays, runs without a shell, returns the child exit code, and never edits the live tracker. The runner orchestrates owned tools; it is not a second task ledger or a source of domain truth.

## Commands

| Command | Current behavior |
| --- | --- |
| `help` / `list` | List supported commands |
| `diagnostics` | Run the redacted environment report |
| `test` | Run `python -m pytest`; missing pytest fails clearly |
| `lint` | Run Ruff when installed; otherwise report unavailable |
| `type-check` | Run mypy when installed; otherwise report unavailable |
| `bootstrap` | Report the Windows bootstrap dependency until PL-0029 provides it |
| `build` | Report deferred platform build work; it does not pretend to build |

Examples:

```powershell
python tools/tasks.py help
python tools/tasks.py diagnostics
python tools/tasks.py test
```

The runner does not install dependencies, select an external engine, mutate system settings, invoke a shell command string, or replace `TASKS.md`. Tool versions, dependency locking, quality configuration, and platform builds remain owned by their separate M01 tasks or later milestones.
