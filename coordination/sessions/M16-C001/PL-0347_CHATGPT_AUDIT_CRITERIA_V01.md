# PL-0347 - ChatGPT Audit Criteria V01

Task: **Windows CI for Python lint, type and unit tests**

All criteria mandatory.

1. Windows production CI exists with least-privilege permissions and explicit timeout.
2. Uses Python 3.12 + locked repository dependencies and fails on lock drift.
3. Runs Ruff check/format, mypy and default locked pytest suite.
4. PR and relevant push triggers are deterministic and do not expose secrets.
5. Existing preview workflow is not silently repurposed as production evidence.
6. Workflow YAML/static checks and repository tests cover task-runner/CI contract where practical.

7. Scope remains inside PL-0347 and accepted predecessor seams; no later-child/M17+ implementation.
8. Builder evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0347_CODEX_PROMPT_V01.md
