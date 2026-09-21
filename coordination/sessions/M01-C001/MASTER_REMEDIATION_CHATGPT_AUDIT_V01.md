# M01-C001 — Master Remediation ChatGPT Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Master remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Master remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V01.md
Master Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_REMEDIATION_CODEX_LOG_V01.md

## Child remediation verdicts

### AUDITED_PASS

- PL-0024
- PL-0025
- PL-0030
- PL-0034
- PL-0036
- PL-0037
- PL-0041

### CHANGES_REQUIRED

- PL-0026 — default Windows paths are fixed, but supported cache/data overrides can still recreate unsafe ancestor/descendant overlap.
- PL-0031 — strict-marker behavior is fixed, but TESTING.md still claims `strict_markers = true` instead of the actual `--strict-markers` addopt; source/log/docs are inconsistent.
- PL-0035 — production cleanup is improved, but the Windows descendant-process regression uses `os.kill(pid, 0)`, which is destructive on Windows and can erase the leaked process it is meant to detect.
- PL-0043 — hosted XCTest wiring is structurally corrected, but the frozen work order required a durable static regression check and only ad-hoc PowerShell validation was performed.

## Master criterion disposition

1-9: PASS  
10: **FAIL** — PL-0026 did not independently pass V02.  
11: PASS  
12: **FAIL** — PL-0031 did not independently pass V02.  
13: PASS  
14: **FAIL** — PL-0035 did not independently pass V02.  
15-16: PASS  
17: **FAIL** — PL-0043 did not independently pass V02.  
18-21: PASS  
22: **FAIL** — cache/data ownership is not invariant under supported explicit overrides.  
23: PASS  
24: **FAIL** — Windows descendant cleanup is not independently proven by a non-destructive regression.  
25-30: PASS  
31: **FAIL** — some builder claims are not fully consistent with independently inspected source/tests/documentation.  
32: **FAIL** — M01 still has four frozen-scope remediation findings.

Result: **24 / 32 PASS, 8 FAIL**

## Independent evidence notes

- Official Python documentation states that on Windows, `os.kill` signal values other than CTRL_C_EVENT/CTRL_BREAK_EVENT cause unconditional termination through TerminateProcess. Therefore `os.kill(pid, 0)` is not accepted as a non-mutating liveness probe.
- Apple build-setting/application-unit-test documentation corroborates that the PL-0043 BUNDLE_LOADER / TEST_HOST / ENABLE_TESTABILITY wiring itself is now structurally correct. The remaining PL-0043 defect is the missing durable static regression guard.

## Required next action

Do not reopen accepted remediation children.

Create and execute a second remediation batch containing only:
- PL-0026 V03
- PL-0031 V03
- PL-0035 V03
- PL-0043 V03

Each child must retain its permanent PL ID, produce a separate V03 Codex log, and be independently re-audited before final M01 closure.

Do not start M02.

Decision: **CHANGES_REQUIRED**
