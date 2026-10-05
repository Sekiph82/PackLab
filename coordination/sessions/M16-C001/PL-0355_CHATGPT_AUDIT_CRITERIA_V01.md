# PL-0355 - ChatGPT Audit Criteria V01

Task: **Resolve/cache SPM dependencies including NextLevel**

All criteria mandatory.

1. Package.resolved or equivalent exact SPM resolution is checked and deterministic.
2. NextLevel 0.19.1 identity matches Xcode project requirement.
3. Cache key binds dependency resolution and relevant runner/Xcode identity.
4. Cache hit cannot bypass dependency resolution validation.
5. No signing/private artifacts cached.
6. License register remains consistent with selected NextLevel package.

7. No M17+ implementation, private data, secret leakage or unreviewed dependency.
8. Implementation/evidence and log publication are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0355_CODEX_PROMPT_V01.md
