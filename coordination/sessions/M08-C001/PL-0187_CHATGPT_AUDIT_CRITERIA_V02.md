# PL-0187 — ChatGPT Audit Criteria V02

Task: **Implement deterministic PackLab-owned mask post-processing after accepted SAM 2.1 raw output**

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_V02.md

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md
- https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0004-sam2.1-segmentation-backend.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CODEX_PROMPT_V02.md

All criteria are mandatory.

1. Live `TASKS.md` authorizes M08-C001 / PL-0187 V02 / READY / CODEX before implementation; PL-0186 is independently accepted; PL-0188+ and M09 remain unauthorized.
2. Implement a PackLab-owned, deterministic, versioned post-processing pipeline limited to:
   - bounded hole filling;
   - bounded edge cleanup;
   - bounded small-component removal.
3. The pipeline consumes a valid parent `MaskArtifact` and produces a new mask revision. It never mutates or overwrites the parent mask, RAW_CAPTURE, source image bytes or PL-0186 raw model evidence.
4. Parent ancestry is explicit and provenance-bound. The child records at least:
   - parent artifact/revision identity;
   - pipeline version;
   - exact parameter set;
   - before/after foreground counts;
   - hole/component cleanup evidence appropriate to the implementation;
   - source image identity/digest;
   - unchanged source coordinate transform semantics.
5. Post-processing identity is deterministic. Same parent + same pipeline version + same parameters yields the same output mask digest/revision identity regardless of execution order or platform.
6. Parameters are explicit and bounded. Invalid, negative, non-finite, excessive or dimension-incompatible values fail closed. No hidden magic defaults may silently change provenance.
7. Empty masks, full masks, edge-touching components, interior holes, diagonal/adjacent components and threshold boundary cases are handled deterministically and tested.
8. Edge cleanup is conservative. It must not become aggressive contour smoothing, geometry fitting, resizing, resampling, topology reconstruction or PL-0190 object-geometry cleanup.
9. Source coordinate dimensions and top-left pixel convention are preserved. If any operation would require resampling, it is outside PL-0187 unless explicitly represented by the existing mask coordinate contract and proven safe.
10. PL-0186 SAM 2.1 runtime/model/checkpoint code remains untouched unless a minimal model-agnostic integration seam is strictly necessary. No SAM-specific logic is added to the post-processing algorithm.
11. No new hosted service, model/runtime/checkpoint download, unreviewed dependency, native binary, private scan, generated reconstruction media or later-task implementation is introduced.
12. Tests through the public boundary include at least:
    - deterministic output/revision;
    - parent immutability;
    - source-byte immutability;
    - parent provenance ancestry;
    - hole fill under/at/over thresholds;
    - small-component removal under/at/over thresholds;
    - conservative edge cleanup boundary cases;
    - empty/full masks;
    - unsafe dimension/parameter rejection;
    - PL-0184/PL-0186 segmentation regressions.
13. If new core contract fields are required, they are backward-compatible with accepted `MaskArtifact` / `MaskSetRevision` behavior and tested without changing downstream authority classes.
14. Focused tests, relevant predecessor regressions, exact locked full pytest suite, Ruff/format, targeted/relevant mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote visibility checks are complete and truthful.
15. Codex does not edit `TASKS.md`, owner ADRs or ChatGPT audit/criteria artifacts.
16. Publish a separate implementation/evidence commit and a separate log-only commit:
    https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CODEX_LOG_V02.md
17. The log records exact algorithms, bounded parameters, ancestry/revision scheme, changed files, focused/full/static checks, limitations and commit SHAs, and ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Do not start PL-0188.
