# PL-0229 - ChatGPT Audit Criteria V01

Task: **Detect and report mesh holes before repair**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0229_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, clean synchronization, accepted M09 partial frontier and owner physical-validation deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement deterministic hole/boundary-loop detection on mesh geometry without repairing anything. Report each hole's loop identity, perimeter, approximate area/extent/location in current coordinates, support evidence and whether it touches uncertain/coverage-gap regions where known. Bound traversal/work. Point-cloud-only inputs must return an explicit unsupported/not-applicable disposition rather than fabricated holes.
3. Tests/evidence cover at minimum: closed mesh no holes, one/multiple holes, boundary ordering, degenerate/open mesh, point-cloud unsupported disposition, bounded work, deterministic report.
4. Parent captured evidence remains immutable; child/proxy/repair revisions preserve exact ancestry, inherited scale state and `DEFERRED_OWNER_VALIDATION` where applicable. No METRIC_VERIFIED, physical accuracy, mold/manufacturing or AI-authority claim is invented.
5. No unreviewed dependency/model/hosted service/private evidence/later-child or M11+ implementation is introduced. PL-0225 dependency changes require exact lock/license/capability evidence.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and completed child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not audit acceptance.
