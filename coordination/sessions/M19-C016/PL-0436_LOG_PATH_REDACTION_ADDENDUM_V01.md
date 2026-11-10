# PL-0436 Log Path Redaction Addendum V01

Date: 2026-11-04

A consolidated M19 privacy review found owner-specific absolute checkout paths in the PL-0436 V03–V08 Codex execution logs. V08 also contained two exact task-local AppData TEMP roots. To reduce disclosure if these implementation records are later shared, only those environment-specific path strings were replaced with generic labels. Each affected log contains an inline notice pointing here.

No command, commit SHA, test result, skip count, RAM measurement, disk-free-space measurement, task status, or validation conclusion was changed. In V08, TEMP root A denotes the successfully cleaned duplicate-JSON retry root and TEMP root B denotes the earlier failed-attempt root; both were already reported absent. Their absolute paths are intentionally not repeated here.

This is evidence hygiene only. It does not alter source or audit verdicts. The logs remain local, and PL-0436 V08 still prohibits source publication to `main`.
