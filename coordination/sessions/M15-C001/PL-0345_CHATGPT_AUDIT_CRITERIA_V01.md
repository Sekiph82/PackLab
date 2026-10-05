# PL-0345 - ChatGPT Audit Criteria V01

Task: **Library backup/export and restore validation**

All criteria are mandatory.

1. Versioned portable backup manifest covers canonical state/audit plus required local binary assets with digests.
2. Archive paths are safe relative and deterministic; traversal/absolute/symlink/duplicate-name attacks reject.
3. Validate-only verifies schema, budgets, digests and audit-chain integrity without mutation.
4. Restore is atomic into empty/new root and leaves no partial state on failure.
5. Existing nonempty destination is not overwritten silently; no network recovery.
6. Tests cover round trip, corrupt/tampered/missing/extra files, zip bombs/bounds and rollback.

7. Scope remains inside PL-0345 and accepted predecessor seams; no later-child/M16+ implementation.
8. Focused/full/static/security/dependency/remote evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0345_CODEX_PROMPT_V01.md
