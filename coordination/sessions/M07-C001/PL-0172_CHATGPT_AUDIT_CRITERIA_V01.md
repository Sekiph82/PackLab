# PL-0172 - ChatGPT Audit Criteria V01

Task: **Export sparse model/cameras in formats needed by OpenMVS and debugging**

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0171_CHATGPT_AUDIT_V01.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0172_CODEX_PROMPT_V01.md

All criteria below are mandatory.

1. Root `TASKS.md` authorizes M07-C001 / `READY` / `CODEX` for PL-0172 before
   material work; PL-0171 remains `AUDITED_PASS`, PL-0068 remains
   `OWNER_REQUIRED`, and PL-0173+ remains unauthorized.
2. The implementation is a bounded PackLab-owned export boundary over the
   accepted PL-0170 `SparseMappingRun` and PL-0171 diagnostic/result contracts,
   with no change to immutable PackScan authority, backend neutrality,
   provenance, or the COLMAP 3.12.6 adapter.
3. Export requires an explicit successful run and explicit immutable payload;
   it never infers sparse content from an asset identity, stdout/stderr, or
   engine discovery, and it rejects failed/cancelled/invalid results.
4. Camera, image, point, and track records validate finite values, unique
   positive IDs, safe relative image names, valid camera references, RGB and
   reprojection bounds, non-dangling tracks, and explicit source/revision/
   request/output provenance.
5. `cameras.txt`, `images.txt`, and `points3D.txt` follow the documented COLMAP
   text semantics with stable ordering, deterministic numeric formatting,
   required image-record line structure, UTF-8 output, and no private paths or
   credentials.
6. The debug manifest is deterministic and machine-readable, records contract
   version, provenance, engine identity, camera convention, counts, relative
   artifact names, and limitations, and makes no filesystem, metric, dense,
   or CAD authority claim.
7. The returned bundle is immutable and non-mutating: it contains only relative
   artifact names and content, performs no arbitrary filesystem write, engine
   invocation, OpenMVS conversion, health probe, or third-party CLI discovery.
8. Public-boundary tests cover valid export, deterministic serialization,
   ordering/formatting, provenance binding, malformed numeric and structural
   records, duplicate/dangling references, unsafe names, failed/cancelled
   runs, redaction, non-mutation, and regression against the accepted sparse,
   diagnostic, reconstruction/process/engine, feature, and matcher contracts.
9. The exact locked full suite exits 0; warnings, skips, unavailable external
   engines, aggregate-test flakes, and native/physical limitations are reported
   truthfully rather than hidden with skips or xfails.
10. Ruff, targeted mypy, compileall, `git diff --check`, protected-file/scope,
    dependency/lock, privacy/secrets/signing, generated, and binary reviews
    pass truthfully; unchanged repository-wide mypy debt is disclosed.
11. The matching `PL-0172_CODEX_LOG_V01.md` exists, uses full GitHub URLs,
    records exact commands/results/SHAs/limitations and separate publication
    boundaries, and ends exactly `AWAITING_AUDIT`.
12. No PL-0173 preset orchestration, OpenMVS/dense stage or conversion, feature
    or matcher change, image/pixel processing, camera solving, segmentation,
    UI workflow, neural/generative model, metric calibration, schema/dependency
    or lock change, physical/native-device acceptance, tracker edit, ChatGPT
    audit artifact edit, or PL-0173+ implementation is included.

Closure requires a fresh independent ChatGPT audit of the PL-0172
implementation diff, source, tests, and handoff against every criterion.
