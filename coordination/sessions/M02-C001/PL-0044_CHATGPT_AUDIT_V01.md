# PL-0044 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0044_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0044_CHATGPT_AUDIT_CRITERIA_V01.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0044_CODEX_LOG_V01.md

Audited implementation commit: `c488f580849d69a0e55a4301d9afc016fb07af44`

## Independent result

The PackScan ZIP layout, path-safety rules, required/optional namespaces, source-versus-derived authority and version-compatibility direction are well defined.

## Blocking finding

The deterministic ZIP timestamp rule is not frozen precisely enough for a cross-language byte-stable writer contract.

The machine-readable layout currently says:

`"timestamps": "zeroed DOS timestamp where the writer permits it"`

This is ambiguous in two material ways:

1. `where the writer permits it` makes the deterministic timestamp optional, so two conforming writers may legitimately emit different timestamps.
2. `zeroed DOS timestamp` does not identify a valid canonical central-directory date/time. ZIP central-directory timestamps have a DOS-era lower bound; for example Python's standard ZIP implementation clamps pre-1980 values to 1980-01-01 rather than representing an all-zero calendar date.

A later Python writer and Swift writer therefore do not yet have one exact timestamp value they can both implement and test for deterministic package equivalence.

## Criterion disposition

1-6: PASS  
7: **FAIL** — deterministic container metadata is not fully specified.  
8: **FAIL** — compression/timestamp expectations are ambiguous rather than canonical.  
9-10: PASS  
11: **FAIL** — the machine-readable layout is not yet sufficient for later deterministic writers to derive one exact timestamp rule.  
12-17: PASS  
18: **FAIL** — a material cross-language determinism defect remains.

Result: **14 / 18 PASS, 4 FAIL**

## Required remediation

Freeze one valid canonical ZIP timestamp value and require it for every PackScan ZIP entry produced by deterministic writers. Prefer an explicit calendar tuple/value, for example `1980-01-01 00:00:00`, together with any necessary rule for extra timestamp fields.

Also specify whether writers must omit timestamp-related extra fields that could reintroduce nondeterminism.

Update both `schemas/packscan/layout.json` and `docs/packscan/container-layout.md`, and add a focused machine-level regression proving the timestamp rule is exact rather than advisory.

Decision: **CHANGES_REQUIRED**
