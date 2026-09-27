---
coordinationSchema: packlab-coordination/v1
artifactType: codex-log
cycleId: M07-C001
taskId: PL-0170
version: V01
actor: CODEX
status: AWAITING_AUDIT
promptPath: coordination/sessions/M07-C001/PL-0170_CODEX_PROMPT_V01.md
criteriaPath: coordination/sessions/M07-C001/PL-0170_CHATGPT_AUDIT_CRITERIA_V01.md
startingCommit: 1b45e0443b2dbf3538513a8a0807f17a59ab7904
implementationCommit: 4225fe4209ae30bdc3f05d4c77612b5ad13609ee
---

# PackLab Codex Implementation Log V01 - PL-0170

## Authority and inputs read

- Repository: https://github.com/Sekiph82/PackLab
- Live tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
- Agent instructions: https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md
- Auxiliary instructions: https://github.com/Sekiph82/PackLab/blob/main/CLAUDE.md
- Repository overview: https://github.com/Sekiph82/PackLab/blob/main/README.md
- Repository structure: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/REPOSITORY_STRUCTURE.md
- Secrets policy: https://github.com/Sekiph82/PackLab/blob/main/docs/security/SECRETS_POLICY.md
- Testing policy: https://github.com/Sekiph82/PackLab/blob/main/docs/development/TESTING.md
- Coordination protocol: https://github.com/Sekiph82/PackLab/blob/main/coordination/README.md
- Audit policy: https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_POLICY.md
- Audit index: https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_INDEX.md
- Builder policy: https://github.com/Sekiph82/PackLab/blob/main/coordination/BUILDER_AI_POLICY.md
- Definition of Done: https://github.com/Sekiph82/PackLab/blob/main/coordination/DEFINITION_OF_DONE.md
- Session workflow validation: https://github.com/Sekiph82/PackLab/blob/main/coordination/SESSION_WORKFLOW_VALIDATION.md
- Codex log contract: https://github.com/Sekiph82/PackLab/blob/main/coordination/CODEX_LOG_CONTRACT.md
- Active prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CODEX_PROMPT_V01.md
- Matching criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CHATGPT_AUDIT_CRITERIA_V01.md
- Prior accepted PL-0169 audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0169_CHATGPT_AUDIT_V01.md
- Accepted PL-0166 boundary: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0166_CODEX_PROMPT_V01.md
- Accepted PL-0167 boundary: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CODEX_PROMPT_V02.md
- Accepted PL-0168 boundary: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CODEX_PROMPT_V02.md
- Accepted PL-0169 boundary: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0169_CODEX_PROMPT_V01.md
- OpenReality integration architecture: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md
- Accepted ADR-0003: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0003-object-centric-reconstruction-authority.md
- Reconstruction contract: https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0163_RECONSTRUCTION_BACKEND_CONTRACT.md
- M07 engine baseline: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/M07_ENGINE_BASELINE.md

The live tracker authorized M07-C001 / `READY` / `CODEX` for PL-0170 and
pointed to this V01 prompt and criteria. PL-0169 remained accepted, PL-0068
remained `OWNER_REQUIRED`, and PL-0171 and later remained unauthorized.
`TASKS.md` and all ChatGPT audit artifacts were reviewed and intentionally
left unchanged.

## Repository synchronization

- Canonical workspace: `C:\Users\sekip\Desktop\PackLab`.
- Git root: PackLab; branch: `main`.
- Remote: `origin https://github.com/Sekiph82/PackLab.git` for fetch and push.
- Initial `git status --short --branch`: clean; no tracked or untracked owner files.
- `git fetch origin main --prune`: completed successfully.
- Starting `git rev-list --left-right --count HEAD...origin/main`: `0 0`.
- Starting commit: `1b45e0443b2dbf3538513a8a0807f17a59ab7904`.
- No fast-forward was needed; the checkout was already equal to `origin/main`.
- Implementation commit: `4225fe4209ae30bdc3f05d4c77612b5ad13609ee`.
- `git push origin main`: succeeded (`1b45e04..4225fe4 main -> main`).
- Fresh `git rev-parse HEAD` after implementation push: `4225fe4209ae30bdc3f05d4c77612b5ad13609ee`.
- The implementation branch was clean before the separate log was created.

The log-only commit is deliberately not predeclared here because this file is
contained by that future commit. ChatGPT should independently verify the final
log-containing head, remote visibility, changed-file range, and clean status.

## Work performed

In `core/src/packlab_core/sparse_mapping.py`, implemented the PackLab-owned
sparse-mapper boundary:

- `SparseMappingRequest` and `SparseMappingConfig` are immutable, canonical,
  digestable values binding the exact ordered image asset IDs, source revision,
  source SHA-256, matcher-selection SHA-256, configuration asset IDs, and the
  pinned COLMAP `3.12.6` identity.
- Repository-relative asset IDs, revisions, digests, uniqueness, and engine
  identity fail closed; caller sequences are snapshotted and no private
  absolute path is placed in portable request serialization.
- `ColmapSparseMapperAdapter` separates command construction from execution and
  maps only the PackLab-owned configuration to the COLMAP `mapper` command.
  Execution requires an explicitly supplied executable and a matching,
  already-probed `EngineProbeResult` with the pinned version. No discovery,
  installation, download, fallback, or engine execution is introduced outside
  the existing `run_reconstruction_stage` seam.
- `RegisteredImageStatistics` and the explicit
  `packlab.sparse-mapping.stage-summary.v1` contract validate total,
  registered, unregistered, ratio, count bounds, and exact request-image-count
  relationships. Human log sentences and ambiguous/malformed summaries are
  rejected rather than interpreted.
- `normalize_sparse_mapping_result` preserves existing
  `ReconstructionStageResult`/`RunStatus` semantics for success, failure, and
  cancellation. A successful sparse output is exposed only when the process
  succeeds and the machine-readable output/statistics contract validates;
  failed, cancelled, malformed, or mismatched results expose no sparse output.
- Stage evidence remains bounded and portable through the existing redacting
  process seam. No source-image bytes, pixels, camera solving, sparse export,
  OpenMVS, UI, schema, dependency, or later-task orchestration was added.

In `tests/core/test_sparse_mapping.py`, added public-boundary tests for ordered
and immutable provenance binding, unsafe/missing/duplicate inputs, engine
version/probe rejection, explicit command mapping, statistics boundaries and
malformed/inconsistent/overflowed summaries, exact request-count binding,
success/failure/cancellation normalization, output suppression, redacted stage
evidence, serialization/digest determinism, and non-mutation.

## Files changed and scope

Implementation commit `4225fe4209ae30bdc3f05d4c77612b5ad13609ee` modified only:

- `core/src/packlab_core/sparse_mapping.py` — product implementation.
- `tests/core/test_sparse_mapping.py` — public-boundary tests.

The separate log-only publication adds only this file:

- `coordination/sessions/M07-C001/PL-0170_CODEX_LOG_V01.md` — implementation
  evidence log.

No `TASKS.md`, ChatGPT audit artifact, prior prompt/criteria/log/audit, accepted
PL-0166 through PL-0169 file, schema, dependency/lock file, UI file, engine
binary, generated artifact, binary fixture, secret, private scan, supplier
file, or signing material was changed.

## Validation evidence

Each material check below records the expected result and failure condition.

- Focused boundary command:
  `uv run --locked pytest -q tests/core/test_sparse_mapping.py tests/core/test_reconstruction.py tests/core/test_reconstruction_process.py tests/core/test_engine_baseline.py tests/core/test_engine_probe.py tests/core/test_feature_extraction.py tests/core/test_matching.py`.
  Expected exit `0`; failure on any focused or regression test failure. Actual:
  `108 passed in 0.69s`, exit `0`.
- Exact locked full command:
  `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`.
  Expected exit `0`; failure on any test error or failure. Actual:
  `427 passed, 5 skipped, 1 deselected, 2 warnings in 25.46s`, exit `0`.
  Skips were four existing OpenCV-unavailable calibration checks and one
  existing Windows symlink-privilege limitation. Warnings were the two
  existing duplicate-ZIP fixture warnings from `zipfile`.
- Ruff check:
  `uv run --locked ruff check core/src/packlab_core/sparse_mapping.py tests/core/test_sparse_mapping.py`.
  Expected no lint errors; failure on any diagnostic. Actual `All checks
  passed!`, exit `0`.
- Ruff formatting:
  `uv run --locked ruff format --check core/src/packlab_core/sparse_mapping.py tests/core/test_sparse_mapping.py`.
  Expected both files already formatted; actual `2 files already formatted`,
  exit `0`.
- Targeted mypy:
  `uv run --locked mypy core/src/packlab_core/sparse_mapping.py`.
  Expected no errors in the changed implementation; actual `Success: no issues
  found in 1 source file`, exit `0`.
- Compile check:
  `uv run --locked python -m compileall -q core/src/packlab_core/sparse_mapping.py`.
  Expected no output and exit `0`; actual no output, exit `0`.
- Repository-wide mypy:
  `uv run --locked mypy core/src apps/windows-studio/src tools`.
  Expected changed-module cleanliness and an explicit report of pre-existing
  debt. Actual exit `1` with the unchanged 18 errors in
  `core/src/packlab_core/transfer_protocol.py`,
  `core/src/packlab_core/calibration/marker_detection.py`,
  `core/src/packlab_core/packscan/container.py`,
  `apps/windows-studio/src/packlab_studio/import_report.py`, and
  `apps/windows-studio/src/packlab_studio/receiver.py`; the changed module had
  no error and no repository debt was modified.
- Formatting and staged whitespace:
  `git diff --cached --check` and the final staged `git diff --check` review.
  Expected no whitespace errors; actual passed with exit `0`.

## Failure and fix chronology

- The first focused sparse-mapping run reported `1 failed, 24 passed`; the
  failure was a test fixture that reversed a list twice, so its supposed
  reversed request still had the original order. The test was corrected without
  changing product code, and the focused boundary suite passed.
- The first Ruff check identified an unused test import and import ordering;
  Ruff removed the unused import and formatted the two new files. The required
  Ruff check and format check then passed.
- A final review identified that a syntactically valid summary could report a
  total different from the ordered request. The implementation added exact
  request-count binding and a bounded total-image limit, with tests. The final
  focused suite and exact full suite above were rerun after that fix.

## Protected, privacy, negative, and scope checks

- Staged changed-file review contained exactly the two authorized product/test
  paths before the implementation commit and no other path afterward.
- Protected review `git diff --cached --exit-code -- TASKS.md` passed; no
  `TASKS.md` content changed. No `CHATGPT_AUDIT_*`, prompt, criteria, prior
  evidence, or audit artifact was changed.
- Dependency/lock review found no `uv.lock` or `pyproject.toml` change.
- Generated/binary review found no cache, environment, build, distribution,
  bytecode, executable, archive, or other binary change; staged numstat was
  numeric for both text files.
- The staged diff whitespace check passed. A credential/private-key pattern
  scan over the staged diff found no GitHub/API token, cloud credential,
  private-key, signing material, or other secret. The absolute-path strings in
  tests are deliberate negative fixtures; portable request serialization and
  stage evidence remain path-safe/redacted.
- Negative coverage includes empty, duplicate, traversal, absolute, control,
  malformed, mismatched, and unsafe values; unsupported engine/probe versions;
  missing, inconsistent, ratio-invalid, overflowed, human-text, and
  request-count-mismatched summaries; failure/cancellation; output suppression;
  redaction; and non-mutation.
- The changed module contains no image decoding, pixel access, feature or pair
  computation, camera solving, segmentation, mask lifting, UI workflow,
  OpenMVS/dense stage, sparse export, neural/generative model, metric
  calibration, schema change, dependency change, or PL-0171+ implementation.

## Limitations and handoff boundary

- This is Codex builder E1/E2 evidence, not independent ChatGPT E3 audit
  evidence. The matching ChatGPT audit must inspect the pushed implementation
  diff, source, tests, and this log against all frozen criteria.
- No COLMAP executable is installed or executed on this host. The tests use an
  injected already-probed result and injected bounded stage runner for the
  adapter path; actual external-engine installation, native execution, and
  clean-machine behavior remain unverified.
- Native Apple/Xcode/device, physical calibration, signing/account, private
  scan, supplier-data, and production reconstruction acceptance are outside
  this task and are not claimed.
- The implementation provides the stage contract and output-asset identity;
  workspace materialization and filesystem existence/health of an external
  sparse model remain governed by their existing/future workspace boundaries.
- The log-containing commit SHA is intentionally not recorded before its own
  commit, as required by the Codex log contract.

## Handoff

AWAITING_AUDIT
