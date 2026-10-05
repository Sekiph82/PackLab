# PL-0365 - ChatGPT Audit Criteria V01

Task: **Task-ID based changelog generation rules**

All criteria mandatory.

1. Changelog entries are tied to explicit PL task IDs and deterministic ordering.
2. Unknown/duplicate/unaccepted tasks reject for release-ready mode.
3. Commit messages/builder logs are not sole acceptance truth.
4. Categories and human summaries are reviewable and path/private-data free.
5. Known limitations can be carried explicitly.
6. No release/tag is created.

7. No M17 implementation or PL-0368 release publication is pulled forward.
8. Implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0365_CODEX_PROMPT_V01.md
