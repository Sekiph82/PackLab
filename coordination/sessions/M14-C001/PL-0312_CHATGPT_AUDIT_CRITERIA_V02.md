# PL-0312 - ChatGPT Audit Criteria V02

Task: **Curvature/slope analysis with truthful component-level provenance**

All criteria are mandatory.

1. Live tracker authorization, M14 partial audit, PL-0310/0311 accepted contracts, PL-0312 V01 blocker and accepted M13 feature-map authority were read.
2. Exact CAD/BREP surface differential analysis is bounded and deterministic and uses exact CAD source truth rather than preview pixels/mesh indices.
3. Candidate records preserve exact model/BREP/digest/parent/unit and stable component provenance.
4. When feature mapping is AMBIGUOUS/UNRESOLVED, candidate feature ownership remains explicitly AMBIGUOUS/UNRESOLVED, `resolved_feature_id` is null, and contributing semantic feature evidence is retained. No face traversal index, transient native face identity, topology order or tessellation index is promoted to authority.
5. Any derived analysis-region identity is deterministic over the exact pinned source and canonical geometric evidence, explicitly scoped to that BREP revision/digest, and collision/ambiguity fails closed.
6. Tests cover planar/cylindrical/sloped/high-curvature cases, threshold boundaries, the accepted ambiguous revolve fixture, deterministic ordering, bounds/invalid inputs, parent modes, unit states and source immutability.
7. Suggestions remain advisory only and do not create physical-fit, print, mold, manufacturing or accuracy authority. RELATIVE remains relative and mm_unverified remains physically unverified.
8. No M13 authority rewrite, unreviewed dependency, network/runtime download, private evidence, tracker edit, PL-0313+ implementation or M15+ work is introduced.
9. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and V02 log publication are distinct; V02 log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0312_CODEX_PROMPT_V02.md
