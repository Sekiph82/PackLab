# PL-0172 - ChatGPT Audit Criteria V02

Task: **Close the missing cancelled-run public-boundary coverage**

Failed audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0172_CHATGPT_AUDIT_V01.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0172_CODEX_PROMPT_V02.md

All criteria below are mandatory. V01 evidence remains valid unless this
remediation or the fresh audit identifies a material contradiction.

1. Root `TASKS.md` authorizes PL-0172 V02 with `CHANGES_REQUIRED` and
   `Required Actor: CODEX`; PL-0171 remains `AUDITED_PASS`, PL-0068 remains
   `OWNER_REQUIRED`, and PL-0173+ remains unauthorized.
2. The V02 diff is limited to `tests/core/test_sparse_export.py` plus the
   matching V02 Codex log. `core/src/packlab_core/sparse_export.py` and the V01
   implementation/evidence remain unchanged.
3. The changed test constructs a valid cancelled `SparseMappingRun` using the
   accepted `RunStatus.CANCELLED` / `StageStatus.CANCELLED` contract, including
   the cancellation flag and valid exit-code semantics.
4. With an otherwise valid explicit immutable payload, the test proves
   `export_sparse_mapping` rejects the cancelled run and cannot return an
   artifact bundle. The test does not rely on filesystem state, stdout/stderr,
   engine discovery, or external executables.
5. The focused PL-0172/regression suite and the exact locked full suite pass;
   skips, warnings, and unchanged repository limitations are reported
   truthfully without skips or xfails hiding the remediation.
6. Ruff, targeted mypy, compileall, `git diff --check`, protected-file/scope,
   dependency/lock, privacy/secrets, generated, binary, and remote-visibility
   checks pass truthfully; no unrelated repository-wide debt is newly created.
7. `PL-0172_CODEX_LOG_V02.md` exists, uses full GitHub URLs, records the V01
   baseline, exact V02 test/check commands and results, separate publication
   boundaries, limitations, and ends exactly `AWAITING_AUDIT`.
8. No product-code change, PL-0173+ implementation, tracker edit, ChatGPT
   audit artifact edit by Codex, schema/dependency/lock change, UI workflow,
   engine invocation, or external/native/physical acceptance is included.

Closure still requires a fresh independent ChatGPT audit of the V02 test diff,
source, log, and the preserved V01 implementation against every criterion.
