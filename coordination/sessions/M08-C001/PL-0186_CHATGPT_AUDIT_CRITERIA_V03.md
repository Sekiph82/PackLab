# PL-0186 — ChatGPT Audit Criteria V03

Task: **Remediate SAM 2.1 runtime/config provenance binding**

Source audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_V01.md

Owner decision:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0004-sam2.1-segmentation-backend.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CODEX_PROMPT_V03.md

All criteria are mandatory.

1. Live `TASKS.md` authorizes M08-C001 / PL-0186 V03 / CHANGES_REQUIRED / CODEX before material work.
2. Preserve accepted V02 behavior: checkpoint identity/hash gate, local-only runtime, no hosted API/download fallback, point/box prompts, source-grid masks, failure handling, RAW_CAPTURE immutability and PL-0187 boundary.
3. Runtime provenance separates:
   - expected/approved SAM 2 upstream identity; and
   - observed installed runtime/package/source identity.
4. The frozen upstream revision `2b90b9f5ceec907a1c18123530e92e794ad901a4` is never emitted as an observed runtime fact unless the installed runtime is actually verified against that identity.
5. SAM 2 unavailable must report observed package/source identity as unavailable/unknown, not the frozen approved revision.
6. Production capability fails closed when installed SAM 2 identity is mismatched or cannot be verified under the selected runtime form.
7. Exact observable runtime facts are captured where available, including package/source form, module path and version; if the authorized runtime uses an editable/git source checkout, its actual commit must be verified against the approved revision.
8. Config provenance is bound to the config actually executed by SAM 2. PackLab must not validate an unrelated filesystem file while `build_sam2` resolves a different packaged Hydra config.
9. The production capability report/provenance records the actual executed config ID plus a deterministic source-bound identity/digest or equivalent proof tied to the verified SAM 2 runtime.
10. A dummy/lookalike `sam2.1_hiera_b+.yaml` file cannot make the backend available.
11. If `config_path` is retained, it must represent the artifact actually used by runtime execution. Otherwise remove/redesign it so there is one config authority.
12. Checkpoint size and SHA-256 remain exactly:
    - `323606802` bytes
    - `a2345aede8715ab1d5d31b4a509fb160c5a4af1970f199d9054ccfb746c004c5`
13. Tests include at least:
    - SAM 2 unavailable -> observed identity unavailable;
    - verified approved runtime identity -> capability may proceed;
    - mismatched/unverified SAM 2 identity -> unavailable;
    - dummy/lookalike config rejection;
    - executed config identity present in provenance;
    - checkpoint success/mismatch;
    - point/box regressions;
    - malformed output regression;
    - source immutability;
    - no network/auto-download.
14. No PL-0187+, M09, dependency expansion, hosted service, model binary commit, private data or protected lifecycle mutation.
15. Focused tests, relevant regressions, exact locked full suite, Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote visibility checks are complete and truthful.
16. Codex does not edit `TASKS.md`, ADR-0004 or ChatGPT audit/criteria artifacts.
17. Publish a separate implementation/evidence commit and a separate log-only commit:
    https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CODEX_LOG_V03.md
18. The V03 log records exact changed files, runtime/config identity strategy, tests, residual limitations and commit SHAs, and ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Closure requires fresh independent ChatGPT audit. Do not start PL-0187.
