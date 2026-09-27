# PL-0173 - ChatGPT Audit Criteria V01

Task: **Build a tunable reconstruction preset system rather than hardcoding CLI flags**

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0172_CHATGPT_AUDIT_V02.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0173_CODEX_PROMPT_V01.md

All criteria below are mandatory.

1. Root `TASKS.md` authorizes M07-C001 / `READY` / `CODEX` for PL-0173 before
   material work; PL-0172 remains `AUDITED_PASS`, PL-0068 remains
   `OWNER_REQUIRED`, and PL-0174+ remains unauthorized.
2. The implementation is a bounded PackLab-owned, backend-neutral preset
   boundary over the accepted feature-extraction, matcher, sparse-mapping,
   reconstruction, and export contracts; accepted predecessor behavior is not
   rewritten.
3. `ReconstructionPreset` and its initial packaged-consumer-goods preset are
   immutable, versioned, explicitly typed, safely identified, bounded, and
   documented as configuration rather than physical benchmark evidence.
4. Non-mutating overrides and construction reject unknown/unsupported fields,
   absolute or private paths, unsafe identities, non-finite values, conflicting
   aliases, and engine-specific CLI keys; equivalent mapping orders normalize
   identically.
5. Canonical serialization includes the complete PackLab-owned preset in stable
   JSON form and produces a deterministic SHA-256 digest independent of input
   mapping insertion order.
6. The public configuration view preserves PackLab provenance and component
   contracts while leaving COLMAP/OpenMVS option names inside existing adapter
   boundaries; no engine discovery, installation, invocation, filesystem
   materialization, or external executable is used.
7. The preset does not claim dense reconstruction, CAD authority, metric
   calibration, `METRIC_VERIFIED`, or any authority beyond explicit
   configuration, and remains compatible with the accepted job/request model.
8. Public-boundary tests cover valid defaults, immutable/non-mutating behavior,
   deterministic serialization/digest, insertion-order equivalence, valid and
   invalid overrides, alias conflicts, unsafe paths/identities, engine-flag
   rejection, component compatibility, and regression against the accepted
   feature/matcher/sparse/diagnostic/export/reconstruction/process/engine
   contracts.
9. The exact locked full suite exits 0; warnings, skips, unavailable external
   engines, aggregate-test limitations, and native/physical limitations are
   reported truthfully without skips or xfails hiding the task.
10. Ruff, targeted mypy, compileall, `git diff --check`, protected-file/scope,
    dependency/lock, privacy/secrets/signing, generated, and binary reviews
    pass truthfully; unchanged repository-wide mypy debt is disclosed.
11. The matching `PL-0173_CODEX_LOG_V01.md` exists, uses full GitHub URLs,
    records exact commands/results/SHAs/limitations and separate publication
    boundaries, and ends exactly `AWAITING_AUDIT`.
12. No engine execution/orchestration, OpenMVS/dense stage, feature or matcher
    execution change, image/pixel processing, camera solving, segmentation,
    UI workflow, neural/generative model, metric calibration, schema/
    dependency/lock change, physical/native-device acceptance, tracker edit,
    ChatGPT audit artifact edit, or PL-0174+ implementation is included.

Closure requires a fresh independent ChatGPT audit of the PL-0173
implementation diff, source, tests, and handoff against every criterion.
