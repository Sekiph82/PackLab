# M02-C001 — Master ChatGPT Audit Criteria V01

Repository: https://github.com/Sekiph82/PackLab
Milestone: M02 — PackScan Data Contract & Calibration

All criteria are mandatory for full M02 closure.

1. TASKS.md authorized M02-BATCH-001 / CODEX.
2. Child execution follows PL-0044 through PL-0068 order without skipping a failed/blocked child.
3. Every attempted child has a frozen prompt, matching audit criteria, implementation/evidence boundary and separate Codex log.
4. Codex did not edit TASKS.md or create ChatGPT audit verdicts.
5. No M03 work was started.
6. PackScan schema/layout/version/checksum contracts are mutually coherent across PL-0044 through PL-0055.
7. Python PackScan implementation and Swift-side writer evidence conform to the same schemas/contracts.
8. Cross-language tests are sensitivity-bearing and do not reduce to string-presence checks.
9. Calibration marker selection, mat geometry, scale math, confidence and profile compatibility use explicit millimetre/unit/provenance conventions.
10. Synthetic calibration evidence is deterministic and catches unit/coordinate/math regressions.
11. No private scan/confidential supplier/credential/signing/cache material entered public Git.
12. Each independently audited child PL-0044 through PL-0067 is AUDITED_PASS before full milestone closure.
13. PL-0068 has real physical owner-controlled benchmark evidence and independently passes; otherwise M02 remains OWNER_REQUIRED and cannot close.
14. MASTER_CODEX_LOG_V01.md accurately indexes the batch and matches actual GitHub history.
15. M02 has no remaining material defect within its frozen scope.

## Audit procedure

ChatGPT must persist one child audit to GitHub before starting the next child audit. After all closable children are audited, ChatGPT writes the milestone audit and updates TASKS.md. Physical benchmark acceptance remains owner-controlled where evidence requires owner action.
