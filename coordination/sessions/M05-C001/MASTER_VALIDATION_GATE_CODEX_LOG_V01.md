# M05-BATCH-005 — Full-Suite Validation Gate Codex Log V01

Milestone: **M05 — Transfer & Ingest**
Repository: https://github.com/Sekiph82/PackLab
Canonical tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
Previous master audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_V03.md
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_VALIDATION_GATE_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_VALIDATION_GATE_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and boundary

- `TASKS.md` authorized M05-BATCH-005 / READY / CODEX for the final six validation-held children: PL-0119, PL-0121, PL-0122, PL-0125, PL-0126 and PL-0134.
- Starting synchronized commit after safe fast-forward: `1040f5a`.
- Implementation/evidence commit: `a6480ba`.
- Changed file: `tests/core/test_subprocess_runner.py` only.
- No M05 product source, iOS source, transfer/ingest behavior, `TASKS.md` or ChatGPT audit artifact was edited.
- No M06 work or PL-0068 physical evidence was started or fabricated.

## Pre-fix failure and root cause

The prior aggregate run at the end of M05-BATCH-004 recorded this exact failure:

```text
_______________ test_windows_liveness_query_is_non_destructive ________________
E           AssertionError: assert False
E            +  where False = _is_process_alive(29428)
E            +    where 29428 = <Popen: returncode: None args: [...]>.pid
tests\core\test_subprocess_runner.py:100: AssertionError
```

The unchanged helper queried Windows `tasklist` through a separate text/CSV process with a hard one-second timeout and mapped `TimeoutExpired` or incomplete output to `False`. Under aggregate-suite load, that made a live owned process look dead. The same helper passed in isolation, which is consistent with a load-sensitive observation race rather than a product-process failure.

## Stabilization

- Replaced the load-sensitive `tasklist` text scrape with a direct, non-destructive Windows `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)` plus `GetExitCodeProcess` query.
- Added a bounded two-second retry window for transient process-start/query availability; no signal, kill, mutation or `shell=True` is used.
- Kept dead-process detection explicit by asserting the queried PID is no longer live after the test-owned process is terminated and waited.
- The six M05 product surfaces were not rewritten.

## Validation evidence

- Repeated liveness proof: 10 consecutive executions, each `1 passed`.
- Surrounding file: `python -m pytest -q tests/core/test_subprocess_runner.py` → `9 passed`.
- Focused M05 regression: `PYTHONPATH=core/src;apps/windows-studio/src python -m pytest -q tests/transfer/test_wire_transport_harness.py tests/transfer/test_loopback_receiver.py tests/transfer/test_protocol.py` → `12 passed`.
- Exact locked suite: `PYTHONPATH=core/src;apps/windows-studio/src python -m pytest -q` → `219 passed, 4 skipped, 1 deselected, 2 warnings`, exit code 0.
- `ruff check tests/core/test_subprocess_runner.py` → passed.
- `python -m compileall -q tests/core/test_subprocess_runner.py` → passed.
- `git diff --check` → passed.
- Protected-file review → `TASKS.md` and all ChatGPT audit artifacts unchanged.
- Secrets/private-material review → no credentials, private keys, signing material or private scans introduced.

## Handoff

The final locked-suite blocker is stabilized with test-infrastructure-only evidence. Independent ChatGPT re-audit remains required for the six held M05 children and this validation gate.

AWAITING_MILESTONE_AUDIT
