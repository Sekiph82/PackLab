# PL-0299 - ChatGPT Audit Criteria V02

Task: **Single-source OBJ/GLB export after assembly-authority conflict resolution**

All criteria are mandatory.

1. M13-C001-R01 tracker authorization, M13 partial audit, accepted PL-0296 authority and M12 metadata-only assembly contract were read.
2. OBJ/GLB export consumes one exact CAD preview/tessellated Design Model source and preserves exact Design Model, BREP, parent-authority, unit and physical-validation metadata.
3. Deterministic OBJ export has stable semantic part naming and valid geometry/index structure.
4. Deterministic GLB export has stable node/part naming, valid GLB structure and explicit reversible scale/axis transform metadata when a transform is applied.
5. RELATIVE/reconstruction_units remains relative; mm_unverified remains physically unverified; no unit transform upgrades authority.
6. The metadata-only M12 assembly hierarchy is not treated as geometry. Assembly/multipart export is not required; attempts to use metadata-only hierarchy as geometry fail closed.
7. No new assembly geometry authority, unreviewed dependency, private evidence, M14+ work or silent network/runtime download is introduced.
8. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and V02 log commits are separate; V02 log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0299_CODEX_PROMPT_V02.md
