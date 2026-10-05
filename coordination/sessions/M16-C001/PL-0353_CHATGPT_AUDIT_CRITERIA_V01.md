# PL-0353 - ChatGPT Audit Criteria V01

Task: **CI without proprietary sample scans**

All criteria mandatory.

1. Default CI/build/smoke succeeds using repository-safe synthetic/public fixtures only.
2. No owner-local path/private scan dependency exists in workflows/tests.
3. Guard detects prohibited private/proprietary data dependency patterns without false claims of M17 benchmark coverage.
4. No private scan bytes are added to Git or artifacts.
5. M17 golden-dataset/accuracy work is not pulled forward.
6. Full suite remains green under clean public-repo assumptions.

7. Scope remains inside PL-0353 and accepted predecessor seams; no later-child/M17+ implementation.
8. Builder evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0353_CODEX_PROMPT_V01.md
