# PL-0031 — ChatGPT Strict Remediation Audit V03

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CHATGPT_AUDIT_CRITERIA_V02.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CODEX_LOG_V02.md
Prior re-audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CHATGPT_AUDIT_V02.md

Audited implementation commit: `a53a7f2af90ff9cd952b55078795b4f225894296`
Audited log commit: `b3879558c7bf6c7252d9bba519be790e9b40394d`

## Result

The original strict-marker defect is technically corrected. The canonical pytest configuration now uses:

`addopts = ["--strict-markers", "-m", "not slow"]`

and the focused regression creates an intentionally unknown marker and verifies collection fails. Registered unit/integration/slow markers and default slow exclusion remain intact.

## Blocking documentation/evidence mismatch

`docs/development/TESTING.md` states:

> The canonical configuration sets `strict_markers = true`

That is not the actual configuration. The remediation log correctly records that `strict_markers` was rejected by the locked pytest version and replaced with the supported `--strict-markers` addopt, but then incorrectly claims the documentation names the actual strict option.

The behavior is correct; the documentation/evidence is not.

## Criterion disposition

1-11: PASS  
12: **FAIL** — documentation does not accurately describe the actual strict-marker configuration mechanism.  
13-21: PASS  
22: **FAIL** — source/log/documentation are not mutually consistent.

Result: **20 / 22 PASS, 2 FAIL**

## Required remediation

No pytest behavior change is required. Update `docs/development/TESTING.md` to state that canonical strict marker validation is enabled by the `--strict-markers` addopt. Preserve the existing marker registrations, default `not slow` behavior, and unknown-marker regression.

Then publish a new remediation log/evidence cycle without rewriting unrelated files.

Decision: **CHANGES_REQUIRED**
