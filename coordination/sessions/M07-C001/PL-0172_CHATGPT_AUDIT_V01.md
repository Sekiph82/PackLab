---
coordinationSchema: packlab-coordination/v1
artifactType: chatgpt-audit
cycleId: M07-C001
taskId: PL-0172
version: V01
actor: CHATGPT
verdict: CHANGES_REQUIRED
promptPath: coordination/sessions/M07-C001/PL-0172_CODEX_PROMPT_V01.md
criteriaPath: coordination/sessions/M07-C001/PL-0172_CHATGPT_AUDIT_CRITERIA_V01.md
codexLogPath: coordination/sessions/M07-C001/PL-0172_CODEX_LOG_V01.md
auditedBase: c24c6f854aa1417d8437881740a5bbaf1874af5b
implementationCommit: 6800c5a6d971cc397314a8825c9e9c47219743a9
auditedHead: fcc5cd51560e8838d3a76c4f55681cab9b3174b1
---

# PL-0172 independent audit V01

## Verdict

`CHANGES_REQUIRED`

The implementation is bounded and the exporter itself rejects non-successful
runs, but the mandatory public-boundary test coverage is incomplete. The
frozen criteria explicitly require failed/cancelled-run coverage; the changed
test file covers a failed run and does not contain a cancelled-run export test.
This is a test/evidence-only remediation. The permanent PL-0172 task remains
open and no product-code defect is asserted by this finding.

## Scope audited

- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`
- Live tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0172_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0172_CHATGPT_AUDIT_CRITERIA_V01.md
- Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0172_CODEX_LOG_V01.md
- Authorization/base commit: `c24c6f854aa1417d8437881740a5bbaf1874af5b`
- Implementation commit: `6800c5a6d971cc397314a8825c9e9c47219743a9`
- Audited remote head / log-only commit: `fcc5cd51560e8838d3a76c4f55681cab9b3174b1`
- Implementation diff: https://github.com/Sekiph82/PackLab/compare/c24c6f854aa1417d8437881740a5bbaf1874af5b...6800c5a6d971cc397314a8825c9e9c47219743a9
- Full audited range: https://github.com/Sekiph82/PackLab/compare/c24c6f854aa1417d8437881740a5bbaf1874af5b...fcc5cd51560e8838d3a76c4f55681cab9b3174b1

## Independent evidence

The canonical checkout is `C:\Users\sekip\Desktop\PackLab`, on `main`, with
origin `https://github.com/Sekiph82/PackLab.git`. Fetch succeeded; local HEAD,
`origin/main`, and the remote `refs/heads/main` were verified at
`fcc5cd51560e8838d3a76c4f55681cab9b3174b1`. The worktree was clean before
audit publication.

The implementation commit changes exactly:

- `core/src/packlab_core/sparse_export.py`
- `tests/core/test_sparse_export.py`

The separate log-only commit changes exactly the required
`PL-0172_CODEX_LOG_V01.md`. `TASKS.md`, accepted predecessor artifacts,
schemas, dependency/lock files, generated files, binaries, private scans,
supplier material, signing material, UI code, and later-task code are outside
the audited implementation range.

Independent validation reproduced:

```text
uv run --locked pytest -q tests/core/test_sparse_export.py tests/core/test_sparse_mapping.py tests/core/test_sparse_diagnostics.py tests/core/test_reconstruction.py tests/core/test_reconstruction_process.py tests/core/test_engine_baseline.py tests/core/test_engine_probe.py tests/core/test_feature_extraction.py tests/core/test_matching.py
171 passed in 1.03s

QT_QPA_PLATFORM=offscreen; uv run --locked pytest -q -rs
490 passed, 5 skipped, 1 deselected, 2 warnings in 38.65s

uv run --locked ruff check core/src/packlab_core/sparse_export.py tests/core/test_sparse_export.py
All checks passed!

uv run --locked ruff format --check core/src/packlab_core/sparse_export.py tests/core/test_sparse_export.py
2 files already formatted

uv run --locked mypy core/src/packlab_core/sparse_export.py
Success: no issues found in 1 source file

uv run --locked python -m compileall -q core/src/packlab_core/sparse_export.py tests/core/test_sparse_export.py
exit 0
```

Repository-wide mypy independently reports the same 18 errors in five
unchanged files; no changed file is among them. `git diff --check`, protected
`TASKS.md` review, changed-path review, and the secrets scan passed. The full
suite skips remain the unavailable `cv2` checks and the Windows symlink
privilege limitation; the existing duplicate-ZIP fixture warnings remain
truthfully visible. No COLMAP/OpenMVS executable, native Apple environment,
physical device, clean-machine environment, or filesystem-materialization
bridge was used or claimed.

## Criteria matrix

| # | Result | Independent disposition |
|---:|---|---|
| 1 | PASS | Live `origin/main` authorized M07-C001 / `READY` / `CODEX` for PL-0172; PL-0171 is independently accepted, PL-0068 remains `OWNER_REQUIRED`, and PL-0173+ was unauthorized during implementation. |
| 2 | PASS | The implementation diff is limited to a PackLab-owned sparse export boundary and its tests; accepted PackScan, backend-neutral, provenance, and COLMAP adapter contracts are not modified. |
| 3 | PASS | `export_sparse_mapping` requires an explicit `SparseMappingRun` and `SparseExportPayload`; `_validate_run` requires a successful sparse stage and does not read stdout/stderr or discover engines. |
| 4 | PASS | Record constructors and `_validate_payload` cover finite values, bounded positive IDs, safe relative names, camera references, RGB/error bounds, bidirectional track integrity, and run-bound source/revision/request/output/engine provenance. |
| 5 | PASS | The source emits the three documented COLMAP text artifacts in UTF-8 with stable field order, sorted camera/image/point records, deterministic numeric formatting, and two image lines per image. Generated comments contain no private path or credential data. |
| 6 | PASS | The sorted JSON manifest includes contract/version, provenance, engine, convention, counts, relative artifact names, and explicit filesystem/metric/dense/CAD limitations without claiming those authorities. |
| 7 | PASS | Frozen dataclasses, tuple normalization, and a mapping-proxy view return an in-memory immutable bundle; the source has no filesystem write, engine invocation/discovery, OpenMVS conversion, health probe, or run/payload mutation path. |
| 8 | CHANGES_REQUIRED | `tests/core/test_sparse_export.py` covers valid/deterministic output, ordering, provenance, malformed records, duplicate/dangling references, unsafe names, failed runs, redaction assertions, non-mutation, and regressions, but has no cancelled-run export test. The mandatory failed/cancelled coverage is therefore incomplete. |
| 9 | PASS | The exact locked full suite independently exited 0 with the disclosed skips and warnings. |
| 10 | PASS | Ruff, targeted mypy, compileall, diff, protected-file/scope, dependency/lock, privacy/secrets, generated, and binary reviews passed truthfully; unchanged repository-wide mypy debt is disclosed. |
| 11 | PASS | The matching log exists at the published path, uses full GitHub URLs, records exact commands/SHAs/limitations and separate publication boundaries, and ends exactly `AWAITING_AUDIT`. |
| 12 | PASS | The audited range contains no PL-0173+ implementation, dense/OpenMVS stage, UI, image processing, calibration, schema/dependency change, tracker edit, or Codex-authored ChatGPT audit artifact. |

## Required remediation

Add one explicit public-boundary test in `tests/core/test_sparse_export.py`
that constructs a valid cancelled `SparseMappingRun` using the accepted
reconstruction/run contract and proves `export_sparse_mapping` rejects it even
when an otherwise valid explicit payload is supplied. The test-only correction
must be published under the V02 prompt and matching criteria; preserve the
implementation boundary and all accepted V01 evidence.

## Audit decision

PL-0172 remains unchecked with `CHANGES_REQUIRED`. The next authorized action
is the bounded PL-0172 V02 test/evidence remediation. No later M07 task is
authorized by this audit.
