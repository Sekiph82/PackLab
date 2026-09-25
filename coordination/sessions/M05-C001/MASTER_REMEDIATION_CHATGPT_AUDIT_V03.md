# M05-BATCH-004 — ChatGPT Master Remediation Audit V03

Decision: **CHANGES_REQUIRED**

Milestone: **M05 — Transfer & Ingest**
Batch: **M05-BATCH-004**
Repository: https://github.com/Sekiph82/PackLab
Codex master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_LOG_V03.md
Final published commit at audit start: `60fd993f4057fe450f88988e2c6cadbfd5521e0c`

## Independent result

All six remaining M05 children were independently audited against final `main`, their V04 criteria, production source, tests and child logs.

### Functional status

The task-specific remediations are acceptable:

- **PL-0119:** real Scan History Finalize action now invokes the canonical accepted-session finalization path and reaches exported history/Share eligibility.
- **PL-0121:** Swift negative decoder matrix now uses the correct status/control/completion/error model and stable error classes.
- **PL-0122:** pairing lifecycle now handles active, stop-refused and already-idle camera states correctly, with conditional restore and wrong-version offer coverage.
- **PL-0125:** production URLSession client completion validation is covered for transfer ID, digest, authenticated, verified, terminal state and declared-digest mismatch.
- **PL-0126:** fake production-client matrix covers retryable digest failure, terminal failure, cancel/retry, same-ID resume and verified completion behavior.
- **PL-0134:** executable HTTPS harness now reloads persisted sender state after a fresh sender instance, verifies receiver/digest identity and certificate fingerprint, applies the Swift-equivalent completion gate, resumes after receiver restart and proves exactly-once ingest.

No new task-specific product defect was found.

## Mandatory blocker

The frozen M05-BATCH-004 audit criteria say **all criteria are mandatory**.

Criterion 15 requires:

> Full locked suite and relevant project/static checks pass truthfully.

Codex reports the exact full-suite run with:
- 218 passed
- 4 skipped
- 1 deselected
- **1 failure**

Failing test:
`tests/core/test_subprocess_runner.py::test_windows_liveness_query_is_non_destructive`

The same test passes in isolation, and the full suite excluding only that test passes. Source inspection shows the test helper invokes Windows `tasklist` with a hard 1.0-second timeout and treats `TimeoutExpired` as “process is dead,” making aggregate-load false negatives plausible.

Because the exact mandatory full-suite gate is not green, none of the final six children can be checked yet despite their task-specific remediation being acceptable.

## Child decisions

| Task | Decision | Reason |
| --- | --- | --- |
| PL-0119 | CHANGES_REQUIRED | Functional remediation passes; held only on full-suite gate |
| PL-0121 | CHANGES_REQUIRED | Functional remediation passes; held only on full-suite gate |
| PL-0122 | CHANGES_REQUIRED | Functional remediation passes; held only on full-suite gate |
| PL-0125 | CHANGES_REQUIRED | Functional remediation passes; held only on full-suite gate |
| PL-0126 | CHANGES_REQUIRED | Functional remediation passes; held only on full-suite gate |
| PL-0134 | CHANGES_REQUIRED | Functional remediation passes; held only on full-suite gate |

## Next action

Authorize **M05-BATCH-005** as a narrow validation-gate stabilization batch.

The goal is not to rewrite M05 product logic. Diagnose and stabilize the unchanged Windows liveness test/proof so it remains non-destructive and deterministic under full-suite load, then rerun the exact locked suite with zero failures.

M05 remains open.
M06 remains blocked.
PL-0068 remains OWNER_REQUIRED.

Decision: **CHANGES_REQUIRED**
