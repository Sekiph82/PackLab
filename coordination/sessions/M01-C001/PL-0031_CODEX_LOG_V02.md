# PL-0031 Codex Remediation Log V02

- Cycle: M01-C001
- Task: PL-0031 — Pytest strict marker remediation
- Prior audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CHATGPT_AUDIT_V01.md
- Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CODEX_PROMPT_V02.md
- Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CHATGPT_AUDIT_CRITERIA_V02.md
- Synchronized start: `46f77d4a394c51f457863c2692179a48c00a5494`; `HEAD...origin/main` was `0 0`.
- Implementation/evidence commit: `a53a7f2af90ff9cd952b55078795b4f225894296`

## Defect-to-fix mapping

The V01 finding was that unit/integration/slow markers were registered but unknown marker names were only warnings. The canonical pytest configuration now includes `--strict-markers` in `addopts`, while retaining all three registered markers and the default `-m not slow` selection. The testing documentation now names the actual strict option.

The regression creates an intentionally unknown-marked temporary test and runs pytest with the repository’s canonical `pyproject.toml`; collection fails and identifies the unknown marker. Existing known-marker smoke coverage remains active, and explicit slow selection remains tested.

## Changed files

- `pyproject.toml`
- `tests/test_pytest_markers.py`
- `docs/development/TESTING.md`

## Validation

Expected results and failure conditions:

- `uv run pytest -q tests/test_pytest_markers.py` — expected known-marker and unknown-marker regression to pass. Actual: `2 passed, 1 deselected`.
- `uv run pytest -q tests/test_pytest_markers.py -m slow` — expected explicit slow selection to pass. Actual: `1 passed, 2 deselected`.
- `uv run pytest -q` — expected sibling M01 regression suite to remain green. Actual: `36 passed, 1 deselected`.
- `uv run ruff check core/src apps/windows-studio/src tools tests` — expected no diagnostics. Actual: all checks passed.
- `uv run mypy core/src apps/windows-studio/src tools` — expected no type errors. Actual: `Success: no issues found in 9 source files`.
- `git diff --check` — expected no whitespace errors. Actual: passed.
- `git diff -- TASKS.md` — expected empty. Actual: empty.
- Exact changed-file review — expected only three authorized files. Actual: only those three files changed.
- Protected/privacy review — expected no tracker, secret, private, signing, cache, or generated-artifact changes. Actual: passed.

An initial focused run exposed that `strict_markers` is not a recognized pytest ini key in the locked toolchain and that the subprocess test was not loading the repository config for a test outside the checkout. Fixes: replaced the unsupported key with the allowed canonical `--strict-markers` addopt, used `-c pyproject.toml`, and asserted combined subprocess output. A second run exposed pytest’s collection diagnostic on stdout rather than stderr; the assertion was corrected. Final validation is green.

## Scope and platform limitations

Only PL-0031 configuration, test, and documentation files changed. No M02 work or tracker edit occurred. No native/device/platform evidence was required or fabricated.

## Remote evidence and handoff

Implementation push completed to `origin/main`. After fetch, `HEAD` and `origin/main` resolved to `a53a7f2af90ff9cd952b55078795b4f225894296` with divergence `0 0`.

AWAITING_AUDIT
