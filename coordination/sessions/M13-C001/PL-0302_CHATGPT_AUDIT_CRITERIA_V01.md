# PL-0302 - ChatGPT Audit Criteria V01

Task: **Add export UI distinguishing Scan Mesh from editable Design Model**

All criteria are mandatory.

1. M13 authorization, safe synchronization, M12 AUDITED_PASS and physical-validation deferral were read.
2. Deterministic implementation is limited to: Implement Windows Studio export UI/workflow that clearly separates Scan Mesh/Scan Master export from editable Design Model/CAD export. The UI must show the selected source authority, revision, units/scale status, physical-validation disclaimer and available formats before export. Domain services remain authoritative; UI must not bypass CAD validation, RELATIVE->mm guards, or export manifest creation. Scan Mesh export must route only through accepted scan export services; Design Model export must route through M13 CAD/export services. No ambiguous single 'Export' action that hides source type.
3. Tests/evidence cover at minimum: source-type selector/summary; Scan Mesh vs Design Model labels; format gating; RELATIVE mm-export disabled/rejected; mm_unverified disclaimer; exact revision display; domain-service delegation; cancel/error path; no authority mutation.
4. Exact source authority/revisions and unit state are preserved; no RELATIVE->mm or unverified->physical/mold/manufacturing authority escalation occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log commits are separate; final child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0302_CODEX_PROMPT_V01.md
