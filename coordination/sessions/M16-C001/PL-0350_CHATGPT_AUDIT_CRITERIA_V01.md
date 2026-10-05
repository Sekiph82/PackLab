# PL-0350 - ChatGPT Audit Criteria V01

Task: **Versioned Windows EXE/installer with redistribution inventory**

All criteria mandatory.

1. Versioned production EXE and installer use canonical Studio version/build revision.
2. Actual staged-file inventory is machine-generated/reviewable and binds hashes/versions where feasible.
3. Required PySide6/Qt, OCP/OCCT/OCP-proxy, Open3D/native and other shipped license/notice texts are packaged and registered.
4. Installer excludes private data/checkpoints/external engines unless explicitly authorized.
5. No release-ready claim if redistribution inventory/notice gate is unresolved.
6. Installer script/build evidence is reproducible and path-portable.

7. Scope remains inside PL-0350 and accepted predecessor seams; no later-child/M17+ implementation.
8. Builder evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V01.md
