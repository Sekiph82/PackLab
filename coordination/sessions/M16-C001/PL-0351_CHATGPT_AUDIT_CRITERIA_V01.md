# PL-0351 - ChatGPT Audit Criteria V01

Task: **Packaged Windows application smoke test**

All criteria mandatory.

1. Smoke exercises packaged production bits rather than source interpreter only.
2. Verifies startup/core imports/Qt initialization/build identity and clean exit.
3. Is deterministic, noninteractive and independent of owner/project/private data.
4. No network/external-engine requirement.
5. Failure returns nonzero and cannot be hidden by process-code ambiguity.
6. Installer smoke, if implemented, uses isolated CI location and cleans up.

7. Scope remains inside PL-0351 and accepted predecessor seams; no later-child/M17+ implementation.
8. Builder evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CODEX_PROMPT_V01.md
