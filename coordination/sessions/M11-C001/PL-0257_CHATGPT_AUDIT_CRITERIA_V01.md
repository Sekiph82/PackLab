# PL-0257 - ChatGPT Audit Criteria V01

Task: **Calculate scan-to-design deviation and expose problem regions**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0257_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. M11 tracker/master authorization, accepted M10 predecessor and M09 deferral were read and synchronization was safe.
2. Deterministic PackLab-owned implementation is limited to: Use accepted M10 scan-to-design comparison services to calculate Design Model deviation against the exact pinned Scan Master and summarize problem regions by feature/height/section. Do not duplicate or weaken M10 authority gates. Values remain geometry-deviation diagnostics in inherited units and are not manufacturing tolerances while physical validation is deferred.
3. Tests cover at minimum: zero/known deviation, feature-region aggregation, stale model parent, open/signed limitations, deterministic region ranking, mm_unverified labeling, no tolerance claim.
4. Exact Scan Master parent remains immutable; Design Model is separate parametric authority; derived preview/deviation evidence does not become Scan Master or manufacturing truth; scale/deferred status is preserved.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M12+ work is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation and log publication are separate; log ends `READY_FOR_INDEPENDENT_AUDIT`.

Independent audit inspects actual source/diff/evidence; builder validation is not acceptance.
