# PL-0019 — ChatGPT Strict Child Audit Criteria V01

Task: **PL-0019 — Create top-level folders for the canonical monorepo**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0019_CODEX_PROMPT_V01.md

All **19 criteria** are mandatory.

1. M01-BATCH-001 / CODEX authorization existed before material work.
2. Repository freshness/synchronization was checked and unsafe Git operations were not used.
3. Root TASKS.md was not edited by Codex.
4. No M02 task or future product behavior was pulled into this child.
5. No secret, credential, private scan, confidential supplier asset, personal signing identity, cache or unsafe generated artifact was committed.
6. Actual changed files are bounded to authorized outputs plus only technically necessary justified adjacent files.
7. Prior accepted M00 artifacts and earlier accepted M01 child outputs were not gratuitously rewritten.
8. Physically create the canonical top-level monorepo areas defined by REPOSITORY_STRUCTURE.md without adding application implementation is satisfied.
9. Use harmless placeholder files only where Git requires a file to materialize an otherwise empty directory is satisfied.
10. Preserve the ownership boundary: iOS presentation/device code under apps/ios-capture, Windows presentation under apps/windows-studio, reusable domain logic under core, contracts under schemas, public-safe assets only under assets, tests under tests, tooling under tools is satisfied.
11. Do not add private scans, supplier files, generated reconstruction output, dependencies, build artifacts, or new architecture is satisfied.
12. Task-relevant focused validation is present and meaningful rather than a no-op.
13. git diff --check passes and builder TASKS.md diff is empty.
14. Changed-file/protected-file/privacy review passes.
15. Platform-specific evidence is truthful; unavailable macOS/Xcode/device evidence is not fabricated.
16. Child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0019_CODEX_LOG_V01.md and links the full prompt/criteria URLs.
17. Child log records synchronized start, implementation/evidence commit, files changed, validations, failures/fixes, scope/privacy, limitations and push evidence.
18. Child log does not self-assign AUDITED_PASS, does not predeclare its future log SHA, and ends READY_FOR_INDEPENDENT_AUDIT.
19. Actual GitHub diff/source/log are mutually consistent and no material task defect remains.

## Closure

ChatGPT independently inspects the actual GitHub commit range, changed files, source/configuration semantics, child log, architecture, security/privacy, regressions and evidence quality. Builder-run local commands remain E1/E2 until independently reproduced or corroborated.

Any failed mandatory criterion keeps PL-0019 open. A child failure does not erase already accepted earlier child audits, but M01 remains open.
