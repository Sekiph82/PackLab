# PL-0031 — ChatGPT Independent Re-Audit V02

Decision: **CHANGES_REQUIRED**

Reason for re-audit: new independent upstream pytest evidence materially affects the prior V01 verdict.

Repository: https://github.com/Sekiph82/PackLab
V01 audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CHATGPT_AUDIT_CRITERIA_V01.md

## New blocking evidence

The current pyproject registers unit/integration/slow markers, but it does not set strict_markers = true and does not include --strict-markers in pytest addopts.

Official pytest documentation states that registered markers avoid warnings for those known markers, while unknown/unregistered markers remain warnings unless strict_markers / --strict-markers is enabled. The PackLab documentation and builder log claim strict marker handling, but the configuration does not enforce it.

Therefore criterion 10 is not satisfied as implemented, and the claimed strict-validation behavior is materially overstated.

## Updated criterion disposition

1-9: PASS
10: **FAIL** — unknown marker typos are warnings, not errors.
11-19: PASS
20: **FAIL** — source/log/docs claim strict handling that the config does not enforce.

Updated result: **18 / 20 PASS, 2 FAIL**

## Required remediation

Enable strict marker validation in the canonical pytest configuration, preferably with strict_markers = true or --strict-markers. Add a regression proving an intentionally unknown marker fails collection, while unit/integration/slow remain registered and the default slow exclusion remains intact.

Prior V01 audit remains historical evidence but is superseded by this V02 re-audit because new independent evidence invalidated that verdict.

Decision: **CHANGES_REQUIRED**
