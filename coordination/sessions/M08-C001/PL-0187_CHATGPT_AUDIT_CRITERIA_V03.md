# PL-0187 - ChatGPT Audit Criteria V03

Task: **Remediate parent raster/digest integrity before deterministic mask post-processing**

Source audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CHATGPT_AUDIT_V01.md

Accepted predecessor:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_V02.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CODEX_PROMPT_V03.md

All criteria are mandatory.

1. Live `TASKS.md` authorizes M08-C001 / PL-0187 V03 / CHANGES_REQUIRED / CODEX before material work; PL-0188+ and M09 remain unauthorized.
2. Preserve all accepted V02 behavior:
   - dependency-free PackLab-owned pipeline;
   - 4-connectivity;
   - bounded hole filling;
   - bounded small-component removal;
   - single synchronous conservative edge cleanup;
   - deterministic parameters and child identity;
   - source/parent immutability;
   - no resizing/resampling;
   - no model/runtime/checkpoint changes.
3. Before reading or processing any in-memory parent raster, prove:
   `parent.raster.digest == parent.mask_digest`.
4. A parent artifact carrying inconsistent raster bytes and declared `mask_digest` fails closed before any child artifact, child identity, child path, processing evidence or derived raster is produced.
5. Prefer enforcing the invariant generically in `MaskArtifact` whenever `raster is not None`. If that would break accepted serialization/runtime behavior, enforce it at minimum in the PL-0187 processing boundary and document why.
6. Matching raster/digest parents remain accepted without changing existing valid serialized mask behavior.
7. Child ancestry remains bound to the actual processed parent:
   - parent artifact ID;
   - parent revision;
   - parent mask digest;
   - source image identity/digest;
   - source dimensions/transform.
8. Deterministic child identity remains unchanged for the same legitimate parent + same parameters + same pipeline version.
9. Existing hole/component/edge semantics and thresholds remain unchanged unless a test exposes a correctness bug directly related to the integrity fix.
10. Tests include at least:
    - matching parent raster/digest accepted;
    - mismatched parent raster/digest rejected;
    - mismatch produces no child/evidence;
    - raw SAM mask artifacts with valid digest/raster still work;
    - already post-processed artifacts with valid digest/raster still validate;
    - deterministic identity regression;
    - parent/source immutability;
    - hole/component/edge regression coverage.
11. No PL-0188+, M09, dependency expansion, hosted service, private data, checkpoint/model binary or protected lifecycle mutation.
12. Focused tests, relevant PL-0184/PL-0186/PL-0187 regressions, exact locked full pytest suite, Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote visibility checks are complete and truthful.
13. Codex does not edit `TASKS.md`, owner ADRs or ChatGPT audit/criteria artifacts.
14. Publish a separate implementation/evidence commit and a separate log-only commit:
    https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CODEX_LOG_V03.md
15. The V03 log records the integrity boundary chosen, tests, changed files, residual limitations and commit SHAs, and ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Do not start PL-0188.
