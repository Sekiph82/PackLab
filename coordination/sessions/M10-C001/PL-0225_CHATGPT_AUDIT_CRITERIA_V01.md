# PL-0225 - ChatGPT Audit Criteria V01

Task: **Integrate Open3D behind a PackLab-owned geometry-analysis adapter**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0225_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, clean synchronization, accepted M09 partial frontier and owner physical-validation deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Select and pin a Python-3.12/Windows-compatible Open3D package only after proving it installs and imports in the locked PackLab environment. Update dependency/lock/license evidence for the exact artifact selected. Add a PackLab-owned adapter/capability layer so no downstream domain contract depends directly on Open3D classes. Probe version/build/capability truthfully; no runtime auto-download. If no compatible reviewed package exists, stop BLOCKED rather than faking support.
3. Tests/evidence cover at minimum: exact version/build probe, Windows/Python 3.12 compatibility, adapter conversion round-trip for point clouds/meshes, unavailable capability, dependency/license record, no runtime download, no domain leakage.
4. Parent captured evidence remains immutable; child/proxy/repair revisions preserve exact ancestry, inherited scale state and `DEFERRED_OWNER_VALIDATION` where applicable. No METRIC_VERIFIED, physical accuracy, mold/manufacturing or AI-authority claim is invented.
5. No unreviewed dependency/model/hosted service/private evidence/later-child or M11+ implementation is introduced. PL-0225 dependency changes require exact lock/license/capability evidence.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and completed child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not audit acceptance.
