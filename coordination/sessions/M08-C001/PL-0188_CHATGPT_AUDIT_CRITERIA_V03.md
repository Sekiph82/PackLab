# PL-0188 - ChatGPT Audit Criteria V03

Task: **Add manual mask-correction UI and versioned revision handoff**

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CHATGPT_AUDIT_V02.md

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/segmentation.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/mask_postprocessing.py
- https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0188_CODEX_PROMPT_V03.md

All criteria are mandatory.

1. Live `TASKS.md` authorizes M08-C001 / PL-0188 V03 / READY / CODEX before implementation; PL-0187 is independently accepted; PL-0189+ and M09 remain unauthorized.
2. Implement a minimal PackLab-owned domain service for manual mask correction plus a Windows Studio presentation seam. The UI may collect/display edits but must not own mask identity, revision identity, provenance, ancestry, invalidation or source bytes.
3. Manual correction consumes a valid parent `MaskArtifact` and produces a new child revision; it never mutates or overwrites the parent mask, raw SAM result, post-processed mask or RAW_CAPTURE.
4. Before manual correction consumes any in-memory parent raster, it proves `parent.raster.digest == parent.mask_digest` or uses an equivalent shared verified accessor. A mismatched parent fails closed before child derivation.
5. Child revision identity is deterministic over all identity-bearing inputs and includes at least:
   - parent artifact/revision/digest;
   - source image identity/digest;
   - source dimensions/transform;
   - normalized manual edit operation sequence or resulting corrected-mask digest plus canonical editor provenance;
   - manual correction pipeline/version.
6. Creation timestamp and other non-authority metadata are excluded from deterministic revision identity.
7. Manual edit ancestry is explicit and append-only. Existing ancestry is preserved and the new parent revision/editor action is represented without overwriting prior history.
8. Editor identity is explicit, validated and provenance-bound. Blank, malformed, private-secret-derived or environment-implicit identity does not silently enter authoritative revision provenance.
9. Supported edit operations are bounded pixel-domain corrections only. At minimum define deterministic set/paint/erase semantics with safe coordinate bounds; malformed coordinates, invalid values, out-of-bounds edits and unsupported operations fail closed.
10. No resize, resampling, smoothing, geometry fitting, model rerun, post-processing parameter mutation, source rewrite or PL-0189 invalidation orchestration is hidden inside PL-0188.
11. Undo/reject behavior is presentation/session state only until an accepted correction is submitted. Cancelling or rejecting an edit creates no authoritative child revision.
12. The Windows Studio presentation layer is thin:
    - may render source/mask overlay and collect edit commands;
    - delegates validation/revision creation to core/domain service;
    - does not compute authoritative digests or revision IDs;
    - remains testable headlessly/offscreen where practical.
13. Tests through the public boundary include at least:
    - domain correction without a display;
    - deterministic child revision;
    - parent/source immutability;
    - parent raster/digest mismatch rejection;
    - valid set/erase edits;
    - out-of-bounds/malformed edit rejection;
    - no-op/cancel/reject behavior;
    - ancestry/editor provenance;
    - repeated correction chain;
    - PL-0186/PL-0187 regressions;
    - headless/offscreen UI composition or presentation-adapter test where available.
14. Existing `MaskArtifact` authority class and source coordinate semantics remain unchanged. Manual correction does not turn masks into geometry/metrology authority.
15. No unreviewed dependency, hosted service, checkpoint/model/runtime change, private scan, generated reconstruction media or later-task implementation is introduced.
16. Focused tests, relevant predecessor regressions, exact locked full pytest suite, Ruff/format, targeted/relevant mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote visibility checks are complete and truthful.
17. Codex does not edit `TASKS.md`, owner ADRs or ChatGPT audit/criteria artifacts.
18. Publish a separate implementation/evidence commit and separate log-only commit:
    https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0188_CODEX_LOG_V03.md
19. The log records domain/UI boundaries, edit contract, ancestry/revision identity, tests, limitations, changed files and commit SHAs, and ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

If PL-0188 is validation-green, its log is remotely visible, and no stop condition exists, Codex must continue directly to PL-0189 under the active master batch without waiting for an intermediate ChatGPT audit. A failed or blocked child stops the batch.
