# PL-0344 - ChatGPT Audit Criteria V01

Task: **Create new SKU from existing geometry**

All criteria are mandatory.

1. New SKU references existing geometry asset/revision; no geometry duplication/mutation.
2. SKU identity uniqueness and required metadata are validated.
3. Optional artwork references are exact/stale-checked and remain separate presentation authority.
4. Supplier facts on geometry are not duplicated/promoted into SKU-specific factual claims.
5. Workflow commits atomically through library service/audit trail; cancel is no-op.
6. UI/service tests cover create, duplicate ID, cancel, stale artwork and shared-geometry behavior.

7. Scope remains inside PL-0344 and accepted predecessor seams; no later-child/M16+ implementation.
8. Focused/full/static/security/dependency/remote evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0344_CODEX_PROMPT_V01.md
