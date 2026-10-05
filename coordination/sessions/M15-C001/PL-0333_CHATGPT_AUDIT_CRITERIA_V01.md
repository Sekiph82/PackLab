# PL-0333 - ChatGPT Audit Criteria V01

Task: **Separate supplier facts from PackLab estimates**

All criteria are mandatory.

1. Field-level provenance is explicit and required wherever a populated factual/estimated value is represented.
2. SUPPLIER_FACT and PACKLAB_ESTIMATE remain distinguishable in canonical serialization and APIs.
3. Estimate method/provenance is retained; optional confidence is bounded.
4. No estimate is promoted to supplier/verified/certified authority automatically.
5. Edits create immutable successor revisions and preserve prior records.
6. Tests cover provenance changes, invalid combinations, deterministic revisions and no-authority-escalation behavior.

7. Scope remains inside PL-0333 and accepted predecessor seams; no later-child/M16+ implementation.
8. Focused/full/static/security/dependency/remote evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0333_CODEX_PROMPT_V01.md
