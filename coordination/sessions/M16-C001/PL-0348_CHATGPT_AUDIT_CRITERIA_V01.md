# PL-0348 - ChatGPT Audit Criteria V01

Task: **Secret-safe dependency caching**

All criteria mandatory.

1. Cache scope is dependency/tool only and keyed by OS/Python/lock identity.
2. Mutable reconstruction/project/library outputs and secrets/signing material are never cached.
3. Cache miss produces a correct build; cache hit cannot bypass uv --locked validation.
4. Restore-key strategy cannot silently reuse an incompatible dependency graph.
5. No secret values are used in cache key/path.
6. Tests/static inspection document cache include/exclude contract.

7. Scope remains inside PL-0348 and accepted predecessor seams; no later-child/M17+ implementation.
8. Builder evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0348_CODEX_PROMPT_V01.md
