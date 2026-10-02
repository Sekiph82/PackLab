# PL-0203 - ChatGPT Audit Criteria V01

Task: **Estimate global reconstruction scale from physical marker geometry**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0203_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, repository synchronization, accepted M08 predecessor and mandatory pre-reads were present before implementation.
2. The implementation is deterministic, PackLab-owned, provenance-bound and limited to this frozen scope: Implement a reconstruction-scale estimator over PL-0202 camera-bound marker evidence and explicit accepted physical marker geometry. Do not convert the existing image-space mm/pixel estimator directly into a 3D global scale. Derive one global reconstruction-units-to-mm factor from geometry that is actually linked to reconstructed cameras/observations, reject inconsistent/outlier observations under a versioned policy, record used/rejected observations and residuals, and remain METRIC_UNVERIFIED until the physical evidence authority required by PL-0209 is satisfied.
3. Public-boundary tests cover at minimum: exact synthetic scale, noisy observations, inconsistent observations, insufficient evidence, unit/revision mismatch, order determinism, uncertainty/residual evidence.
4. RAW_CAPTURE, accepted M08 authority/revisions and source bytes remain immutable; no AI/generated geometry gains measurement authority and no unsupported physical/metric claim is made.
5. No unreviewed dependency/model/hosted service/private evidence/later-child or M10+ implementation is introduced. Owner-controlled physical evidence is never fabricated.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation and log commits are separate, and the child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Audit must independently inspect the actual GitHub diff/source/evidence. Builder validation is not acceptance. A real failed/blocked/owner-required child stops the M09 batch.
