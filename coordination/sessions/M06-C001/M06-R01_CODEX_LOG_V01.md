# M06-R01 Codex Remediation Evidence Log V01

- Scope: PL-0138, PL-0140, PL-0141, PL-0144, PL-0145, PL-0146, PL-0147, PL-0148 and PL-0149.
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/M06-R01_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/M06-R01_CHATGPT_AUDIT_CRITERIA_V01.md
- Source audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/CHATGPT_AUDIT_V01.md
- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`

## Authorization and publication recovery

- Root tracker authorized `M06-R01 / CHANGES_REQUIRED / CODEX` and pointed to the prompt and criteria above.
- M03–M05 remain accepted, PL-0068 remains `OWNER_REQUIRED`, M07 remains untouched, and PL-0150 through PL-0157 were not started.
- The pre-existing local-only evidence commits were verified as the expected three artifacts and preserved without rewriting: `50b32dcbe432969f8d384b7a195564f93f574986` (PL-0149 log), `a5fad927e8aff07c062243e8e2404cbce8633ab5` (PL-0145 log), and `fea9830505e457cb777dc6885ba06453fbc17478` (master batch-stop log).
- Remote-only commits were the expected independent audit, criteria, prompt and tracker updates. A normal non-destructive merge produced `57a8345beddaf399a360e504f9705ba9780a5268`; no reset, rebase, force-push, destructive clean or stash was used.
- The recovered logs were verified on remote before remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0145_CODEX_LOG_V01.md, https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0149_CODEX_LOG_V01.md and https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_LOG_V01.md.

## Remediation result by task

| Task | Builder result |
|---|---|
| PL-0138 | Remediated production restore: preference loading accepts current work-area bounds, geometry size/position is clamped before `setGeometry`, and an off-screen shell restore test uses the production seam. |
| PL-0140 | Remediated production adapter coverage: `OwnedSubprocessJob` uses only `packlab_core.subprocess_runner`, remains non-terminal until runner cleanup reports, records cleanup failure, and tests prove unrelated cancellation state is untouched. |
| PL-0141 | Remediated production diagnostics: the shell creates bounded local bundles containing safe build/runtime data, project summary, active jobs and structured errors; nested redaction covers secrets and Windows/POSIX private paths. |
| PL-0144 | Remediated lifecycle authority: `ProjectManager` notifies the shell, route/workspace availability is derived from manager state, and active-job replacement is vetoed before a new destination is created. |
| PL-0145 | Publication recovered and verified. No source churn was made because the existing implementation satisfied the requested publication-only remediation boundary. |
| PL-0146 | Remediated crash-safe editable-state/revision publication with an authoritative atomic project authority document and deterministic mirror recovery after injected failure. |
| PL-0147 | Remediated atomic append-only history publication with complete authoritative state, integrity-chain validation, revision continuity checks, atomic mirrors and injected-write-failure coverage. |
| PL-0148 | Remediated ProjectManager/Studio recovery lifecycle: open exposes abnormal recovery items, start establishes active recovery authority, accept/discard remain project-scoped, and clean close marks the session clean. |
| PL-0149 | Remediated deterministic stale/query seams, persisted stale reopen behavior, direct/transitive integrity invalidation and missing/tampered upstream detection without raw mutation. |

## Changed files

- https://github.com/Sekiph82/PackLab/blob/main/apps/windows-studio/src/packlab_studio/diagnostics.py
- https://github.com/Sekiph82/PackLab/blob/main/apps/windows-studio/src/packlab_studio/history.py
- https://github.com/Sekiph82/PackLab/blob/main/apps/windows-studio/src/packlab_studio/jobs.py
- https://github.com/Sekiph82/PackLab/blob/main/apps/windows-studio/src/packlab_studio/navigation.py
- https://github.com/Sekiph82/PackLab/blob/main/apps/windows-studio/src/packlab_studio/preferences.py
- https://github.com/Sekiph82/PackLab/blob/main/apps/windows-studio/src/packlab_studio/project.py
- https://github.com/Sekiph82/PackLab/blob/main/apps/windows-studio/src/packlab_studio/provenance.py
- https://github.com/Sekiph82/PackLab/blob/main/apps/windows-studio/src/packlab_studio/shell.py
- https://github.com/Sekiph82/PackLab/blob/main/apps/windows-studio/src/packlab_studio/subprocess_jobs.py
- https://github.com/Sekiph82/PackLab/blob/main/apps/windows-studio/src/packlab_studio/workspace.py
- https://github.com/Sekiph82/PackLab/blob/main/tests/studio/test_m06_r01.py

## Validation evidence

- Focused remediation and affected-regression tests: `QT_QPA_PLATFORM=offscreen uv run --locked pytest -q tests/studio/test_m06_r01.py tests/studio/test_preferences.py tests/studio/test_shutdown.py tests/studio/test_diagnostics.py tests/studio/test_project.py tests/studio/test_project_revision.py tests/studio/test_autosave.py tests/studio/test_history.py tests/studio/test_recovery.py tests/studio/test_provenance.py tests/studio/test_shell.py tests/studio/test_navigation.py tests/studio/test_workspace.py` -> `44 passed`.
- Exact full locked suite: `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q` -> `272 passed, 4 skipped, 1 deselected, 2 warnings`.
- Warnings were the two pre-existing duplicate ZIP-entry warnings in https://github.com/Sekiph82/PackLab/blob/main/tests/packscan/test_container.py and https://github.com/Sekiph82/PackLab/blob/main/tests/transfer/test_validation_gate.py.
- `uv run --locked ruff check apps/windows-studio/src/packlab_studio tests/studio` -> passed.
- Targeted mypy for all changed Studio modules -> passed.
- `uv run --locked python -m compileall -q core/src apps/windows-studio/src tests/studio` -> passed.
- `git diff --check` -> passed; protected `TASKS.md` remained unchanged; `pyproject.toml` and `uv.lock` remained unchanged.
- Full configured mypy was also run. It remains red only in pre-existing unrelated core/import-report/receiver annotations (`18` errors across five files); no changed R01 module is among those errors. This limitation is not claimed as a pass.
- Secrets, privacy, raw-evidence, signing-material and generated/binary review found no new prohibited material. No native, GPU, reconstruction or physical-device claim was made.

## Commits and handoff

- Publication-recovery merge: https://github.com/Sekiph82/PackLab/commit/57a8345beddaf399a360e504f9705ba9780a5268.
- Remediation implementation/evidence commit: https://github.com/Sekiph82/PackLab/commit/109138a96e11e71584c06082bb4a4e39117fd14a.
- This file is the sole content of the separate final log-only commit; its SHA is recorded in the final publication verification after commit and push.
- The builder evidence is not independent acceptance. ChatGPT must re-audit the remote source, tests, recovered artifacts and criteria before any task is closed or PL-0150 is authorized.

READY_FOR_INDEPENDENT_AUDIT
