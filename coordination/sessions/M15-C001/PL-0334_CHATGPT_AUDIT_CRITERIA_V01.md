# PL-0334 - ChatGPT Audit Criteria V01

Task: **Link scans, Scan Master and Design Models**

All criteria are mandatory.

1. Packaging Asset can link plural raw scans, zero/one Scan Master and multiple Design Model revisions.
2. Every link pins exact project and source identity/digest fields available from PackLab contracts.
3. Duplicate/stale/malformed link identities fail closed; one-Scan-Master cardinality is enforced.
4. No geometry bytes or ambient project root is canonical library data.
5. Link changes create deterministic successor asset/library revisions.
6. Tests cover missing/unavailable runtime project resolution without rewriting canonical links.

7. Scope remains inside PL-0334 and accepted predecessor seams; no later-child/M16+ implementation.
8. Focused/full/static/security/dependency/remote evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0334_CODEX_PROMPT_V01.md
