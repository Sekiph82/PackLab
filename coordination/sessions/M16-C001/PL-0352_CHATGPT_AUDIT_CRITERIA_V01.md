# PL-0352 - ChatGPT Audit Criteria V01

Task: **Public-repo artifact retention policy**

All criteria mandatory.

1. Artifact classes have explicit bounded retention and unambiguous names.
2. Public CI artifacts never include private data/signing secrets/keychains/profiles.
3. Required artifacts fail upload when missing instead of silently succeeding.
4. Retention is consistent across Windows/macOS workflows as they are added.
5. Policy is documented outside TASKS.md.
6. No GitHub Actions write permission is added merely for retention.

7. Scope remains inside PL-0352 and accepted predecessor seams; no later-child/M17+ implementation.
8. Builder evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0352_CODEX_PROMPT_V01.md
