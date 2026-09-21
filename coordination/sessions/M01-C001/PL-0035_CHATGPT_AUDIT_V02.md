# PL-0035 — ChatGPT Strict Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CHATGPT_AUDIT_CRITERIA_V02.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CODEX_LOG_V02.md
Prior audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CHATGPT_AUDIT_V01.md

Audited implementation commit: `d9d6f65409c073b10ad0762824736285773606ee`
Audited log commit: `54d6042634a37f1ade3fd863c87451d25758a7a1`

## Blocking finding

The production cleanup path is materially improved: Windows immediately invokes bounded `taskkill /PID <owned-root> /T /F`, while POSIX retains process-group cleanup.

However, the required Windows descendant-process regression is not a valid proof.

The helper used by both timeout and cancellation tests defines liveness as:

`os.kill(pid, 0)`

On POSIX that is commonly a non-destructive existence check. On Windows, Python documents different semantics: `CTRL_C_EVENT` and `CTRL_BREAK_EVENT` are the special console signals; **any other signal value** causes unconditional termination through the Windows `TerminateProcess` API. Therefore using signal value 0 can itself terminate a surviving process.

As a result, the test can erase the exact leaked descendant it is supposed to detect. It can therefore produce a false PASS and would not reliably fail against the pre-remediation parent-only cleanup path.

## Criterion disposition

1-10: PASS  
11: **FAIL** — the parent/child regression does not reliably prove both processes were already terminated by the runner.  
12-14: PASS  
15: **FAIL** — the focused regression can mask the pre-remediation defect by killing the surviving process during its liveness check.  
16-21: PASS  
22: **FAIL** — the log claims descendant disappearance was proven, but the test method is not non-destructive on Windows.

Result: **19 / 22 PASS, 3 FAIL**

## Required remediation

Keep the production `taskkill /T /F` process-tree strategy unless new evidence shows a defect, but replace the Windows liveness assertion with a non-destructive process-existence check.

A suitable test may use a Windows API/process-handle query, a bounded `tasklist`/PowerShell query, or another non-mutating mechanism. It must:
- observe parent and spawned child PIDs without terminating them;
- prove both are gone after timeout;
- prove both are gone after cancellation;
- fail against a deliberately parent-only cleanup implementation;
- avoid broad process matching or terminating unrelated processes.

Also handle/validate the `taskkill` result sufficiently that cleanup failure cannot be silently treated as success.

## Evidence boundary

GitHub production/test source and commit topology were independently inspected as E3. The Windows `os.kill` semantics were independently corroborated against official Python documentation. Builder-run test success is not accepted as proof for the invalid liveness assertion.

Decision: **CHANGES_REQUIRED**
