# PL-0300 - ChatGPT Audit Criteria V01

Task: **Add export manifest for source project, revision, scale and software versions**

All criteria are mandatory.

1. M13 authorization, safe synchronization, M12 AUDITED_PASS and physical-validation deferral were read.
2. Deterministic implementation is limited to: Implement one canonical machine-readable export manifest contract shared by M13 STEP/STL/OBJ/GLB exports. Record project ID, export ID, format, exact Design Model revision, parent-authority kind/root or Scan Master binding, CAD representation revision/digest, source coordinate unit/scale state, any export-space scaling transform, topology-validation result, tessellation settings where applicable, selected Python binding version, observed OCCT/kernel version, PackLab version/commit, file digests, component/part names, named-feature mapping status, physical-validation status and limitations. Manifest identity must be deterministic over export content/provenance, excluding ambient paths/timestamps where inappropriate.
3. Tests/evidence cover at minimum: STEP/STL/OBJ/GLB manifest variants; file SHA-256; parent authority; unit/scale transform; software/kernel versions; topology/tessellation metadata; privacy-safe path handling; deterministic manifest ID; no physical validation escalation.
4. Exact source authority/revisions and unit state are preserved; no RELATIVE->mm or unverified->physical/mold/manufacturing authority escalation occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log commits are separate; final child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0300_CODEX_PROMPT_V01.md
