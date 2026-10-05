# PL-0349 - ChatGPT Audit Criteria V01

Task: **Windows PackLab Studio build job**

All criteria mandatory.

1. Production job packages the real Studio app, not preview/windows/packlab_preview.py.
2. Build tool selection is reproducible and license-reviewed; lock changes are intentional.
3. Artifact contains no private sample data/checkpoints/external engine binaries unless separately authorized.
4. Build revision and Studio version are bound into artifact provenance.
5. Packaged app starts far enough for deterministic smoke preparation without requiring network.
6. CI/build scripts are path-portable and owner-path free.

7. Scope remains inside PL-0349 and accepted predecessor seams; no later-child/M17+ implementation.
8. Builder evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0349_CODEX_PROMPT_V01.md
