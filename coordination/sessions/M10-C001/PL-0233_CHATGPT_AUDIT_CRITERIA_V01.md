# PL-0233 - ChatGPT Audit Criteria V01

Task: **Create Scan Master asset with captured-evidence-only ancestry**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0233_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, safe synchronization, accepted M09 partial frontier and owner deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement the domain Scan Master asset/revision contract and eligibility gate exactly against PL-0233 authority rules. Only captured-evidence ancestry may promote: RAW_CAPTURE -> RECONSTRUCTION_OBSERVATION -> OBJECT_CAPTURE_GEOMETRY -> M09 scale/alignment -> M10 conservative cleanup. Generated/AI_VISUAL_REFERENCE and preview proxies are ineligible. Persist complete promotion manifest, source/output digests, cleanup operations, hole report, scale provenance and alignment. Because physical validation is deferred, inherited scale state must remain unchanged and the Scan Master must explicitly record physical_accuracy_validation_status=DEFERRED_OWNER_VALIDATION and mold_use_authorized=false. Promotion never overwrites source/reconstruction/object geometry.
3. Tests/evidence cover at minimum: eligible captured ancestry, generated/AI rejection, preview proxy rejection, complete manifest, source/output digest, cleanup/hole linkage, immutable parents, deferred physical-validation flag, scale state preservation, deterministic revision identity.
4. RAW_CAPTURE/reconstruction/original captured geometry remain immutable; revision/proxy/repair/export ancestry is explicit, inherited scale state is preserved and `DEFERRED_OWNER_VALIDATION` cannot become physical/mold authority.
5. Generated/AI_VISUAL_REFERENCE cannot become Scan Master authority. No unreviewed dependency/model/hosted/private evidence/later-child or M11+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and completed child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not acceptance.
