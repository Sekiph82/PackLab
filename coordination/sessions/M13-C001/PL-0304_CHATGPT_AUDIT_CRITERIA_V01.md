# PL-0304 - ChatGPT Audit Criteria V01

Task: **Generate section views at user-selected heights/planes**

All criteria are mandatory.

1. M13 authorization, safe synchronization, M12 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic implementation is limited to: Implement deterministic technical-drawing section views from validated CAD/BREP solids at explicit user-selected canonical heights/planes. Record plane definition, intersected components/features, section curves, hatching regions where safely derivable, and empty/no-intersection cases. Section view geometry is drawing evidence derived from CAD representation; it does not alter Design Model or BREP. Bound work and reject invalid/non-finite planes.
3. Tests/evidence cover at minimum: horizontal/vertical section; empty section; multi-component assembly section; deterministic curve ordering; invalid plane; feature/part provenance; optional hatch metadata; no source mutation.
4. Exact Design Model/CAD parent revisions and units remain explicit; no pixel-derived dimensions, RELATIVE->mm promotion or physical/mold/manufacturing claim occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced; PL-0308 must block rather than silently add a PDF dependency.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0304_CODEX_PROMPT_V01.md
