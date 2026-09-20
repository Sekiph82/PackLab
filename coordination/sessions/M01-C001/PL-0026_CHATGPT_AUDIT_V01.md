# PL-0026 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CHATGPT_AUDIT_CRITERIA_V01.md
Builder log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CODEX_LOG_V01.md

Audited implementation commit: `467fc7a354ba107e35740ab4261f43ca7dd6b04d`
Audited log commit: `e2f2891b0607dd18a5f47300b95a132b86929f00`

## Blocking finding

The frozen contract requires cache, temporary job workspace, and durable user/project data to be separated concepts and locations.

On Windows the current defaults are:

- `cache_root() -> %LOCALAPPDATA%/PackLab`
- `workspace_root() -> %LOCALAPPDATA%/PackLab/work`
- `project_data_root() -> %LOCALAPPDATA%/PackLab/data`

Therefore durable project data is physically nested **inside the logical cache root**. This contradicts the policy text stating that durable data uses application-data locations “rather than the cache root” and creates a dangerous future cleanup boundary: any recursive cache-root cleanup would include durable owner data.

macOS/Linux defaults separate cache and data roots correctly; the defect is the Windows default layout.

## Criterion disposition

1-8: PASS  
9: **FAIL** — durable project data is not safely separated from the Windows cache root.  
10-19: PASS  
20: **FAIL** — a material path-boundary defect remains.

Result: **18 / 20 PASS, 2 FAIL**

## Required remediation

Use distinct Windows roots, for example a PackLab parent containing sibling `cache/`, `work/` and `data/`, or another clearly separated platform-appropriate scheme where durable data is never beneath the cache root.

Preserve:
- explicit environment overrides;
- lazy creation;
- no automatic owner-data deletion;
- macOS/Linux separation;
- tests that never touch the real profile.

Add a Windows regression proving `project_data_root` is not equal to, beneath, or inside `cache_root`.

## Evidence boundary

GitHub source, tests, policy text and path semantics were independently inspected as E3. Builder-run local commands remain E1/E2 where not independently rerun.

Decision: **CHANGES_REQUIRED**
