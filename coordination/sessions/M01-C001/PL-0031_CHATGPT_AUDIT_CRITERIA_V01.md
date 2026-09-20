# PL-0031 — ChatGPT Strict Child Audit Criteria V01

Task: **PL-0031 — Configure pytest with unit/integration/slow markers**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CODEX_PROMPT_V01.md

All **20 criteria** are mandatory.

1. M01-BATCH-001 / CODEX authorization existed before material work.
2. Repository freshness/synchronization was checked and unsafe Git operations were not used.
3. Root TASKS.md was not edited by Codex.
4. No M02 task or future product behavior was pulled into this child.
5. No secret, credential, private scan, confidential supplier asset, personal signing identity, cache or unsafe generated artifact was committed.
6. Actual changed files are bounded to authorized outputs plus only technically necessary justified adjacent files.
7. Prior accepted M00 artifacts and earlier accepted M01 child outputs were not gratuitously rewritten.
8. Configure pytest discovery for the monorepo and markers for unit, integration and slow tests is satisfied.
9. Keep default developer test execution fast by excluding slow tests unless requested is satisfied.
10. Register markers so unknown-marker warnings fail or are prevented is satisfied.
11. Document selection commands and CI intent without creating M16 workflows is satisfied.
12. Add at least one marker smoke test or collection check proving configuration is active is satisfied.
13. Task-relevant focused validation is present and meaningful rather than a no-op.
14. git diff --check passes and builder TASKS.md diff is empty.
15. Changed-file/protected-file/privacy review passes.
16. Platform-specific evidence is truthful; unavailable macOS/Xcode/device evidence is not fabricated.
17. Child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CODEX_LOG_V01.md and links the full prompt/criteria URLs.
18. Child log records synchronized start, implementation/evidence commit, files changed, validations, failures/fixes, scope/privacy, limitations and push evidence.
19. Child log does not self-assign AUDITED_PASS, does not predeclare its future log SHA, and ends READY_FOR_INDEPENDENT_AUDIT.
20. Actual GitHub diff/source/log are mutually consistent and no material task defect remains.

## Closure

ChatGPT independently inspects the actual GitHub commit range, changed files, source/configuration semantics, child log, architecture, security/privacy, regressions and evidence quality. Builder-run local commands remain E1/E2 until independently reproduced or corroborated.

Any failed mandatory criterion keeps PL-0031 open. A child failure does not erase already accepted earlier child audits, but M01 remains open.
