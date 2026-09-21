# PL-0035 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CHATGPT_AUDIT_CRITERIA_V01.md
Builder log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CODEX_LOG_V01.md

Audited implementation commit: 58a535dc283783d9797d2ea9abbc810304787624
Audited log commit: b61220907b8a1679fa77a3ed2984b8a79c4c573a

## Blocking finding

The subprocess runner correctly uses argument arrays, shell=False, streaming callbacks, structured results, timeout and cancellation. However, the Windows process-tree cleanup contract is incomplete.

Current Windows stop sequence:

1. process.terminate() terminates only the direct parent process;
2. the code waits up to 250 ms;
3. if the parent exits during that wait, the stop helper returns immediately;
4. taskkill /PID ... /T /F is only executed when the parent itself does not exit within 250 ms.

If the launched parent process has spawned child/grandchild processes and the parent exits promptly after TerminateProcess, those descendants can survive because the tree-kill path is skipped.

This violates the frozen requirement for child-process cleanup appropriate to Windows. The current timeout/cancellation tests use only a single sleeping process and therefore do not prove process-tree cleanup.

## Criterion disposition

1-8: PASS
9: **FAIL** — Windows descendant-process cleanup is not guaranteed.
10-11: PASS
12: **FAIL** — timeout/cancellation tests do not exercise spawned child-process cleanup.
13-19: PASS
20: **FAIL** — a material safe-process-ownership defect remains.

Result: **17 / 20 PASS, 3 FAIL**

## Required remediation

Make Windows process ownership/tree termination explicit and deterministic. A valid approach may use a Windows process group/job-object strategy or always perform a safe tree termination for owned descendants before considering cleanup complete.

Add regression tests that:
- launch a lightweight Python parent that spawns a long-lived Python child;
- trigger timeout and cancellation separately;
- prove both parent and spawned child are terminated;
- retain portable POSIX behavior and shell=False.

Do not solve this with broad system process matching or termination outside the runner-owned process tree.

## Evidence boundary

GitHub source, tests, process-termination control flow and commit topology were independently inspected as E3. Builder-run runtime tests/Git commands remain E1/E2 where not independently rerun.

Decision: **CHANGES_REQUIRED**
