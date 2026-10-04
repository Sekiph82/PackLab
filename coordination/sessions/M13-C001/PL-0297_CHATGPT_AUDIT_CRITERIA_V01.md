# PL-0297 - ChatGPT Audit Criteria V01

Task: **Export Design Model/assembly to STEP with explicit millimetre units**

All criteria are mandatory.

1. M13 authorization, safe synchronization, M12 AUDITED_PASS and physical-validation deferral were read.
2. Deterministic implementation is limited to: Implement deterministic STEP export from a validated M13 CAD/BREP representation for one Design Model or supported assembly. STEP export is permitted only when the source coordinate unit is `mm_unverified`; RELATIVE/reconstruction_units must fail closed rather than silently scaling to millimetres. Write STEP units as millimetres and preserve part/assembly names and stable feature/component labels where the selected binding supports them. Export metadata must state that millimetre units are numerically encoded but physical accuracy remains unverified and mold/manufacturing suitability is not authorized. Preserve exact Design Model revision, CAD representation revision, parent-authority mode and selected CAD/kernel version.
3. Tests/evidence cover at minimum: single-part STEP; assembly STEP if supported by selected binding; mm_unverified source accepted; RELATIVE source rejected; deterministic file/manifest identity; part names; stable feature mapping where available; reopened unit check; no physical/mold claim.
4. Exact source authority/revisions and unit state are preserved; no RELATIVE->mm or unverified->physical/mold/manufacturing authority escalation occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log commits are separate; final child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0297_CODEX_PROMPT_V01.md
