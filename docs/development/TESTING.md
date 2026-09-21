# Python testing strategy

Pytest discovers tests below `tests/` through the root `pyproject.toml`. The canonical configuration enables strict unknown-marker validation through the `--strict-markers` addopt, and three markers are registered:

- `unit` is for fast isolated behavior;
- `integration` is for owned module/tool boundaries;
- `slow` is opt-in and excluded from the default developer run.

## Selection commands

```powershell
python tools/tasks.py test
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m slow
uv run pytest -m "unit or integration"
uv run pytest --collect-only -q
```

The default configuration applies `-m "not slow"`, so a normal `pytest` or task-runner test run stays fast. An explicit `-m slow` selection replaces that default for an intentional slow run. Unknown markers are errors under pytest's strict configuration because all supported markers are registered in `pyproject.toml`.

CI intent is documented only: a future authorized CI task may run the fast suite on every change and opt into integration/slow lanes as appropriate. This task does not create M16 workflows or claim CI execution.
