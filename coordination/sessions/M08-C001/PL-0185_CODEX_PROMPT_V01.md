# PL-0185 - Codex Work Order V01

Task: **Benchmark public/synthetic segmentation candidates and record selection evidence**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M08-C001

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0185_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0185_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0185_CODEX_LOG_V01.md

## Authorization gate

Start only when live TASKS.md explicitly authorizes M08-C001 / READY / CODEX for the complete ordered batch and this child frontier. The predecessor child log must be remotely visible, the package must match origin/main, M07 must remain AUDITED_PASS, PL-0068 must remain OWNER_REQUIRED, and M09/later work must remain unauthorized. Re-read all repository rules and the master prompt before editing; stop on mismatch.

## Frozen scope

Build a reproducible benchmark harness and public-safe synthetic/public fixture set covering bottle, jerrycan, cap, transparent and glossy-like cases. Compare explicitly named candidate capabilities, quality metrics and failure modes; record dataset/provenance, runtime, license and checkpoint/hash facts. Produce a bounded benchmark report and a model-selection recommendation or an explicit no-selection blocker. Do not treat visual similarity as production accuracy.

## Allowed change boundary

- PackLab-owned core contracts/adapters and only the minimal Windows Studio presentation seam required by this child;
- dedicated tests and public/synthetic fixtures or bounded evidence explicitly required by this child;
- coordination/sessions/M08-C001/PL-0185_CODEX_LOG_V01.md.

Do not edit TASKS.md, ChatGPT artifacts, accepted audits, unrelated task code, private/confidential data, RAW_CAPTURE bytes, signing material, or later-milestone code. Do not add unreviewed dependencies, model/checkpoint downloads, hosted APIs or generated reconstruction media. No private scans, supplier assets, automatic model downloads, hosted API, unreviewed checkpoint, production backend implementation, or PL-0186+.

## Required validation and handoff

Run the exact focused tests for this child, relevant predecessor/regression suites, the locked full pytest suite, Ruff/format, targeted/relevant mypy, compileall, git diff --check, protected-file/scope checks, dependency/license/privacy/secrets/generated/binary checks and remote visibility. Record exact commands, expected results, explicit failure conditions, actual results and exit status, including negative/boundary/regression coverage and unavailable native/physical gates. Use a separate implementation/evidence commit and child-log-only commit. End the child log exactly with READY_FOR_INDEPENDENT_AUDIT. Continue only to the next frozen child when green and no stop condition exists.
