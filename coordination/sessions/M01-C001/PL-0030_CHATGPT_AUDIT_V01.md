# PL-0030 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0030_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0030_CHATGPT_AUDIT_CRITERIA_V01.md
Builder log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0030_CODEX_LOG_V01.md

Audited implementation commit: `333eed4eefee81bfcc602e4655a9bfd5119ebc7b`
Audited log commit: `212d9ab2953cf11172a68cffe4f3669823e08ef7`

## Blocking finding

The Ruff/mypy configuration itself is valid and active, but the required root task-runner integration is not reliable in the final M01 environment.

PL-0029 installs the locked developer tools into uv's project environment via `uv sync --locked --dev`. The bootstrap does not activate that environment in the caller's shell. Current `tools/tasks.py` nevertheless implements:

- lint via `shutil.which("ruff")` then direct `ruff check .`
- type-check via `shutil.which("mypy")` then direct `mypy ...`

Therefore a fresh successful bootstrap can leave the documented `python tools/tasks.py lint` and `python tools/tasks.py type-check` commands reporting the tools unavailable even though the locked tools are correctly installed in `.venv`.

The canonical task runner should invoke the locked environment deterministically, for example through `uv run ruff ...` and `uv run mypy ...`, or another equally reproducible project-environment mechanism.

## Criterion disposition

1-9: PASS  
10: **FAIL** — task-runner integration does not reliably invoke the locked quality tools.  
11-19: PASS  
20: **FAIL** — a material M01 developer-command integration defect remains.

Result: **18 / 20 PASS, 2 FAIL**

## Required remediation

Update the root task runner so lint/type-check use the reproducible PL-0029 environment without requiring manual activation. Preserve:
- one canonical pyproject configuration;
- no duplicated lint/type rules;
- argument-array subprocess safety;
- active negative-fixture proof;
- M01-owned formatting scope.

Add focused runner tests proving locked-tool dispatch does not depend on global PATH installation.

## Evidence boundary

GitHub source, current pyproject/bootstrap/task-runner integration, changed files and log evidence were independently inspected as E3. Builder-run local Ruff/mypy/Git commands remain E1/E2 where not independently rerun.

Decision: **CHANGES_REQUIRED**
