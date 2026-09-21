# PL-0026 — ChatGPT Strict Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CHATGPT_AUDIT_CRITERIA_V02.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CODEX_LOG_V02.md
Prior audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CHATGPT_AUDIT_V01.md

Audited implementation commit: `c485f0158e930ee3c117f8a98f932d2fd720b785`
Audited log commit: `f1e0e9d4c4b706e0ead945b429d25022eccc0b93`

## Blocking finding

The default Windows layout is corrected:

- cache: `%LOCALAPPDATA%/PackLab/cache`
- workspace: `%LOCALAPPDATA%/PackLab/cache/work`
- durable data: `%LOCALAPPDATA%/PackLab/data`

However, the frozen remediation criterion requires durable owner data to **never** be beneath the logical cache root while preserving explicit overrides. The current helpers accept `PACKLAB_CACHE_ROOT` and `PACKLAB_DATA_ROOT` independently with no overlap validation.

An advanced configuration such as:

`PACKLAB_CACHE_ROOT=C:\PackLab`
`PACKLAB_DATA_ROOT=C:\PackLab\data`

recreates the original V01 hazard: durable data is once again a descendant of the logical cache root and can be swept by a future recursive cache cleanup.

The new regression test proves only the default Windows layout. It does not exercise unsafe override overlap.

## Criterion disposition

1-7: PASS  
8: **FAIL** — the “durable data is never beneath cache” invariant is not enforced when explicit overrides overlap.  
9-21: PASS  
22: **FAIL** — a material ownership-boundary defect remains under supported override configuration.

Result: **20 / 22 PASS, 2 FAIL**

## Required remediation

Preserve both explicit overrides, but validate the resolved roots before use. Reject unsafe equality/ancestor-descendant overlap between cache and durable project data with an actionable error. The workspace may remain beneath the disposable cache root.

Add Windows and platform-neutral regression tests for:
- cache == data rejection;
- data beneath cache rejection;
- cache beneath data rejection if that arrangement would make ownership ambiguous;
- safe sibling overrides accepted;
- default platform paths remain unchanged;
- all test filesystem operations remain under temporary roots.

Update the policy documentation to state the enforced non-overlap invariant.

## Evidence boundary

GitHub source, tests, policy documentation, implementation/log commits and the supported override semantics were independently inspected as E3. Builder-run local tests remain corroborating E1/E2 evidence where not independently rerun.

Decision: **CHANGES_REQUIRED**
