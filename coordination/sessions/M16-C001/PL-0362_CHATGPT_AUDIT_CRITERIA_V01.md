# PL-0362 - ChatGPT Audit Criteria V01

Task: **Exact iPhone 16 install/reinstall procedure**

All criteria mandatory.

1. iPhone 16 procedure covers prerequisites, signing route, install, permissions, build verification, reinstall/upgrade and troubleshooting.
2. Data-preservation warning precedes destructive uninstall.
3. CI-signed and local-personal-team routes are distinguished.
4. No owner identifiers/credentials/UDIDs.
5. Unsigned artifacts are not described as directly installable.
6. Documentation references artifact provenance/build identity.

7. No M17+ implementation, private data, secret leakage or unreviewed dependency.
8. Implementation/evidence and log publication are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0362_CODEX_PROMPT_V01.md
