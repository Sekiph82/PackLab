# PL-0053 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0053_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0053_CHATGPT_AUDIT_CRITERIA_V01.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0053_CODEX_LOG_V01.md

Audited implementation commit: `0dfc9a890d76183492ee15c54055253dda9dc4ae`

## Independent result

Preview/thumbnail/diagnostics payloads are correctly optional, derived, namespace-bounded and linked through manifest size/SHA-256 metadata. Source image authority is preserved.

## Blocking privacy finding

The diagnostics schema intends to prohibit credential-like messages, but its JSON-Schema regex is case-sensitive:

`(token|password|passwd|secret|api[_-]?key)`

Therefore variants such as `Password=...`, `TOKEN=...` or `ApiKey=...` can remain schema-valid. The log states credential-like forms are rejected, but the committed negative fixture exercises only a private local path and does not test credential leakage.

A public diagnostics contract cannot rely on callers using lowercase secret labels.

## Criterion disposition

1-9: PASS  
10: **FAIL** — credential prohibition is bypassable through casing.  
11: **FAIL** — fixture coverage does not include credential leakage despite the frozen privacy requirement.  
12: **FAIL** — current negative evidence would not detect mixed/uppercase credential labels.  
13-17: PASS  
18: **FAIL** — source/log privacy claims are stronger than the actual schema.

Result: **14 / 18 PASS, 4 FAIL**

## Required remediation

Make credential/private-path rejection casing-robust using portable JSON-Schema regex patterns or another strict schema representation. Add negative fixtures for mixed/uppercase forms such as Password, TOKEN and ApiKey, while preserving legitimate redacted messages and all derived-payload authority/linkage rules.

Decision: **CHANGES_REQUIRED**
