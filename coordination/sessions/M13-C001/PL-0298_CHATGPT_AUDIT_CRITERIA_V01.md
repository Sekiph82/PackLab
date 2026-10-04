# PL-0298 - ChatGPT Audit Criteria V01

Task: **Export printable STL with explicit unit handling and mesh-quality options**

All criteria are mandatory.

1. M13 authorization, safe synchronization, M12 AUDITED_PASS and physical-validation deferral were read.
2. Deterministic implementation is limited to: Implement deterministic STL export from a validated CAD/BREP representation via controlled tessellation. STL has no reliable embedded unit metadata, so printable STL export must require `mm_unverified` source coordinates and produce a mandatory sidecar/export manifest declaring numerical coordinates are interpreted as millimetres but remain physically unverified. RELATIVE sources must fail closed for printable STL. Expose bounded mesh-quality options (deflection/angular tolerance or named presets) that map to explicit tessellation parameters; preserve source revision and topology-validation status. Do not call the STL production-ready or physically accurate.
3. Tests/evidence cover at minimum: binary or explicitly selected STL mode; coarse/fine bounded presets; deterministic triangle output; mm_unverified sidecar; RELATIVE rejection; invalid BREP rejection; triangle/normal sanity; exact source revision; no print-fit/manufacturing claim.
4. Exact source authority/revisions and unit state are preserved; no RELATIVE->mm or unverified->physical/mold/manufacturing authority escalation occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log commits are separate; final child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0298_CODEX_PROMPT_V01.md
