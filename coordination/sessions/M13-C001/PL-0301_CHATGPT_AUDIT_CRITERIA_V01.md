# PL-0301 - ChatGPT Audit Criteria V01

Task: **Add STEP round-trip validation and bounding-dimension recheck**

All criteria are mandatory.

1. M13 authorization, safe synchronization, M12 AUDITED_PASS and physical-validation deferral were read.
2. Deterministic implementation is limited to: Implement deterministic round-trip validation for exported STEP: reopen the exact exported file using the selected CAD adapter, verify readable solid/assembly topology, unit metadata, expected part count/names where supported, and recompute bounding dimensions in the exported coordinate system. Compare round-trip bounds against the pre-export CAD representation using an explicit numerical tolerance derived from serialization/kernel precision, not a physical manufacturing tolerance. Fail closed on unreadable STEP, unit mismatch, missing solids or excessive numerical drift. Preserve the distinction between numerical round-trip fidelity and real-world accuracy.
3. Tests/evidence cover at minimum: known simple revolve/loft round-trip; unit=mm check; bounds within explicit numerical tolerance; corrupted STEP; missing solid; part/name checks where supported; deterministic report; numerical fidelity != physical tolerance.
4. Exact source authority/revisions and unit state are preserved; no RELATIVE->mm or unverified->physical/mold/manufacturing authority escalation occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log commits are separate; final child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0301_CODEX_PROMPT_V01.md
