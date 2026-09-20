# Python quality strategy

PackLab uses the root `pyproject.toml` as the one configuration source for Python quality tools. M01 selects Ruff for linting/formatting and mypy for type checking; the root task runner only invokes these tools and does not duplicate their rules.

## Commands

```powershell
python tools/tasks.py lint
python tools/tasks.py type-check
uv run ruff format --check core/src apps/windows-studio/src tools tests
uv run ruff check core/src apps/windows-studio/src tools tests
uv run mypy core/src apps/windows-studio/src tools
```

Ruff targets Python 3.12, uses a deterministic 100-column line length, and enables focused correctness/import/upgrader rules (`E4`, `E7`, `E9`, `F`, `I`, `UP`). Its formatter uses double quotes, spaces, and LF. Mypy targets Python 3.12, checks function bodies, warns on unused ignores, and ignores missing third-party stubs until package-specific integration is authorized.

Formatting is limited to M01-owned or newly added Python files. It does not authorize rewriting historical files or generated artifacts. The locked dev group supplies the tools; the lock and bootstrap remain PL-0029 evidence.

## Active-check proof

The checks are not a no-op. A deliberately invalid stdin fixture such as `def broken(:` is rejected by `uv run ruff check --stdin-filename intentionally_bad.py -`, while a minimal valid module passes. This proof uses no repository file and leaves no fixture or generated artifact behind.

The Windows checkout records only truthful static/runtime Python-tool evidence. Xcode, iOS, and native platform builds remain outside this task.
