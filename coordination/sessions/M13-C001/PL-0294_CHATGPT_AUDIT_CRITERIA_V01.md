# PL-0294 - ChatGPT Audit Criteria V01

Task: **Validate BREP solid topology and report invalid/non-manifold failures**

All criteria are mandatory.

1. M13 tracker/master authorization, safe synchronization, M12 AUDITED_PASS, ADR-0005 and M09 deferral were read.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement PackLab-owned BREP validation diagnostics using the selected CAD adapter/kernel. Report whether a representation is a valid closed solid where required, shell/solid counts, open/free-edge or invalid topology evidence available from the kernel, boolean/loft/revolve failure status, and feature/revision provenance. Validation must never silently repair the BREP in this child. A CAD representation can be geometrically valid while still physically unvalidated; do not conflate topology validity with manufacturing suitability.
3. Tests/evidence cover at minimum: valid revolved solid; valid loft; open shell; invalid/non-manifold or failed shape; deterministic diagnostics; parent representation binding; no silent repair; topology-valid != physical/mold-ready.
4. CAD/BREP remains derived from exact Design Model revision; parent authority, units and DEFERRED_OWNER_VALIDATION remain explicit; no RELATIVE->mm or unverified->physical/mold authority promotion occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced. PL-0289 alone owns dependency/lock/license selection.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log publication is separate; child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0294_CODEX_PROMPT_V01.md
