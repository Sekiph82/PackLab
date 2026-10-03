# PL-0253 - ChatGPT Audit Criteria V01

Task: **Detect editable body, shoulder, neck and base zones**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0253_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. M11 tracker/master authorization, accepted M10 predecessor and M09 deferral were read and synchronization was safe.
2. Deterministic PackLab-owned implementation is limited to: Detect candidate body/shoulder/neck/base zones from accepted profile/cross-section evidence using explicit deterministic rules. Persist editable boundaries as Design Model feature metadata, with confidence/evidence and manual override revisions. Ambiguous zones remain review-required; no thread/finish classification is introduced.
3. Tests cover at minimum: clear synthetic zones, ambiguous shoulder/neck, boundary ordering, manual override, stale evidence rejection, stable feature IDs, deterministic zone identity.
4. Exact Scan Master parent remains immutable; Design Model is separate parametric authority; derived preview/deviation evidence does not become Scan Master or manufacturing truth; scale/deferred status is preserved.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M12+ work is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation and log publication are separate; log ends `READY_FOR_INDEPENDENT_AUDIT`.

Independent audit inspects actual source/diff/evidence; builder validation is not acceptance.
