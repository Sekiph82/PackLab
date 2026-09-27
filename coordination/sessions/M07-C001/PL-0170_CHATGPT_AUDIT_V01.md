---
coordinationSchema: packlab-coordination/v1
artifactType: chatgpt-audit
cycleId: M07-C001
version: V01
actor: CHATGPT
verdict: CHANGES_REQUIRED
promptPath: coordination/sessions/M07-C001/PL-0170_CODEX_PROMPT_V01.md
criteriaPath: coordination/sessions/M07-C001/PL-0170_CHATGPT_AUDIT_CRITERIA_V01.md
codexLogPath: coordination/sessions/M07-C001/PL-0170_CODEX_LOG_V01.md
auditedBase: 1b45e0443b2dbf3538513a8a0807f17a59ab7904
implementationCommit: 4225fe4209ae30bdc3f05d4c77612b5ad13609ee
auditedHead: 647f27e09eee772654e315168c3015c199991e0b
---

# PL-0170 independent audit V01

## Verdict

`CHANGES_REQUIRED`

The sparse-mapper boundary is substantially implemented and the required
runtime/static gates pass, but the published result boundary does not fail
closed for several malformed or ambiguous stage results. PL-0170 remains
open. PL-0171 and later tasks remain unauthorized.

## Scope audited

- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`
- Live tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CHATGPT_AUDIT_CRITERIA_V01.md
- Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CODEX_LOG_V01.md
- Authorization/base commit: `1b45e0443b2dbf3538513a8a0807f17a59ab7904`
- Implementation commit: `4225fe4209ae30bdc3f05d4c77612b5ad13609ee`
- Audited remote head / log-only commit: `647f27e09eee772654e315168c3015c199991e0b`
- Implementation diff: https://github.com/Sekiph82/PackLab/compare/1b45e0443b2dbf3538513a8a0807f17a59ab7904...4225fe4209ae30bdc3f05d4c77612b5ad13609ee
- Full audited range: https://github.com/Sekiph82/PackLab/compare/1b45e0443b2dbf3538513a8a0807f17a59ab7904...647f27e09eee772654e315168c3015c199991e0b

## Evidence classification

### E1/E2 Codex evidence

The matching log records the authorized prompt and criteria, separate
implementation and log publication commits, exact builder commands, the
unchanged repository-wide mypy debt, limitations, and the final
`AWAITING_AUDIT` marker.

### E3 independent ChatGPT evidence

- Verified the canonical Git root, `main` branch, origin URL, clean status,
  safe fetch, divergence `0 0`, and `HEAD == origin/main` at
  `647f27e09eee772654e315168c3015c199991e0b`.
- `git ls-remote origin refs/heads/main` independently returned
  `647f27e09eee772654e315168c3015c199991e0b`.
- The actual published range contains only
  `core/src/packlab_core/sparse_mapping.py`,
  `tests/core/test_sparse_mapping.py`, and the matching Codex log. No tracker,
  prior prompt/criteria/audit, dependency/lock file, binary, generated output,
  private scan, supplier material, or signing material was changed.
- Independently reran the focused boundary suite: `108 passed`, exit `0`.
- Independently reran `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked
  pytest -q -rs`: `427 passed, 5 skipped, 1 deselected, 2 warnings`, exit `0`.
  The skips are four unavailable-OpenCV checks and one Windows symlink-
  privilege limitation; the two warnings are existing duplicate-ZIP fixture
  warnings.
- Independently reran Ruff, format checking, targeted mypy, compileall,
  `git diff --check`, protected-file checks, and the repository-wide mypy
  comparison. The changed module is clean; repository-wide mypy still reports
  the same 18 errors in five unchanged files.
- Direct public-boundary probes reproduced the findings below.

### E4 owner evidence/decision

None is required for this software-boundary remediation. Native Apple/device,
physical, clean-machine, and actual external-COLMAP execution evidence remains
outside this task and is not claimed.

## Criteria matrix

| # | Result | Evidence / finding |
|---:|---|---|
| 1 | PASS | The live tracker authorized M07-C001 / `READY` / `CODEX` for PL-0170 before implementation; PL-0169 is accepted, PL-0068 remains `OWNER_REQUIRED`, and PL-0171+ remains unauthorized. |
| 2 | PASS | The implementation is PackLab-owned and backend-neutral, uses immutable relative asset identities and source/matcher digests, preserves the existing process seam, and pins COLMAP to 3.12.6 without adding later-stage work. |
| 3 | PASS | `SparseMappingRequest` and `SparseMappingConfig` are frozen, snapshot ordered input IDs, validate relative paths/digests/revision, and provide canonical serialization and SHA-256 identity without private absolute paths. |
| 4 | PASS for request inputs; FAIL for the normalized summary boundary | Request invalid/duplicate/unsafe/mismatched values fail with PackLab-owned errors and caller sequences are not mutated. However, an overflowed numeric summary value escapes as raw `OverflowError`, detailed below. |
| 5 | PASS | The adapter emits only the explicit COLMAP `mapper` command, requires a matching valid probe and pinned version, and uses the existing bounded runner. No discovery, installation, download, fallback, or unrelated engine execution was added. |
| 6 | FAIL | `normalize_sparse_mapping_result` can report success for a result with the wrong `stage_id` or with `status=SUCCEEDED` and `cancelled=True`; it also defaults a missing output identity to the configured path. These are invalid or ambiguous output-contract states. |
| 7 | FAIL | Count bounds and ratio consistency mostly pass, but a huge integer ratio raises raw `OverflowError` instead of `SparseMappingSummaryError`. Conflicting output aliases are also silently ignored rather than rejected. |
| 8 | FAIL | The focused tests cover the ordinary valid/error paths, but do not detect numeric conversion overflow, wrong-stage results, inconsistent cancellation flags, missing output identity, or conflicting output aliases. |
| 9 | PASS | The exact locked full suite independently exits 0 with truthful warnings, skips, and external-engine/native limitations. |
| 10 | PASS | Ruff, format, targeted mypy, compileall, diff-check, scope/protected-file, dependency/lock, privacy/secrets, generated, and binary reviews pass; unchanged repository-wide mypy debt is disclosed. |
| 11 | PASS | The matching log exists with full GitHub URLs, exact SHAs, exact commands/results, separate publication boundaries, limitations, and an exact final `AWAITING_AUDIT` line. |
| 12 | PASS | The published range contains no PL-0171+ work, dense/OpenMVS stage, feature/matcher change, image/pixel processing, UI, model, calibration, schema/dependency/lock change, physical acceptance, tracker edit, or ChatGPT audit artifact from the builder. |

## Findings

### High - malformed numeric summary escapes the PackLab error boundary

`parse_registered_image_statistics` converts a caller-provided numeric
`registration_ratio` with `float(ratio_value)` at
`core/src/packlab_core/sparse_mapping.py:288-294` without translating
`OverflowError` or other conversion failures into the PackLab-owned
`SparseMappingSummaryError`.

Independent reproduction against the published head:

```text
parse_registered_image_statistics({valid_summary, "registration_ratio": 10**1000})
-> OverflowError: int too large to convert to float
```

The value is rejected, but not through the required bounded PackLab diagnostic
contract. It also bypasses the `normalize_sparse_mapping_result` exception
handler, which catches only `SparseMappingError`.

### High - stage identity and cancellation inconsistencies can be reported as success

`normalize_sparse_mapping_result` at
`core/src/packlab_core/sparse_mapping.py:442-476` dispatches on `status` but
does not validate `stage_result.stage_id`, the `cancelled` flag, or the
success/exit-code consistency before returning a successful `SparseMappingRun`.

Independent reproductions against the published head:

```text
ReconstructionStageResult("other", SUCCEEDED, 0, ...)
-> SparseMappingRun.status == SUCCEEDED

ReconstructionStageResult("sparse-mapping", SUCCEEDED, 0, ..., cancelled=True)
-> SparseMappingRun.status == SUCCEEDED
```

An injected or future runner result with the wrong stage identity or a
cancellation contradiction must fail closed; it must not be normalized as a
successful sparse stage.

### High - output identity is optional and ambiguous aliases are not rejected

The normalizer uses `values.get("sparse_model_asset_id", values.get("output_asset_id"))`
and only checks a present value for mismatch. Therefore a valid-looking
statistics summary with no output identity, a primary alias set to `null`, or
conflicting `sparse_model_asset_id` and `output_asset_id` values still returns
`SUCCEEDED` and fills the output from configuration. That does not establish a
valid machine-readable stage output contract and violates the fail-closed
ambiguity boundary.

The public `SparseMappingRun` constructor also does not enforce the exact
request-image-count binding for directly constructed successful results. The
V02 correction must close the invariant both in normalization and in the
published result type, while preserving the existing future workspace
materialization boundary.

## Architecture / regression / security review

The defects are confined to the new sparse-mapping result/summary boundary.
The remediation must preserve valid request construction, canonical digests,
the explicit COLMAP command/probe boundary, existing redacted process
evidence, immutable RAW_CAPTURE authority, and all current regression behavior.
No secret, private scan, supplier file, signing material, binary, dependency,
or lock-file change was found.

## TASKS.md action

Root `TASKS.md` remains unchecked for PL-0170 and is updated by this audit to
`CHANGES_REQUIRED`, with Required Actor `CODEX` and the V02 remediation
prompt/criteria as the next action. PL-0171 remains unauthorized.

## Remediation

The bounded V02 correction is:

1. Translate ratio conversion overflow/invalid conversion into a PackLab-owned
   `SparseMappingSummaryError` and add a public-boundary regression test.
2. Validate the sparse stage identity and status/`cancelled`/exit-code
   consistency before success normalization. Wrong-stage or contradictory
   results must fail closed and expose no sparse output.
3. Require one valid, repository-relative output identity in the documented
   machine-readable summary, reject missing/null/mismatched values, and reject
   conflicting output aliases rather than choosing one silently.
4. Enforce the request-image-count/statistics binding and stage invariants in
   the public successful `SparseMappingRun` result as well as the normalizer.
5. Add behavior-sensitive tests for all findings, including huge numeric
   values, wrong stage IDs, contradictory cancellation flags, nonzero success
   exits, missing/null/conflicting output identities, direct-result invariant
   construction, and the existing valid success/failure/cancellation paths.
6. Rerun the V02 focused, relevant boundary, full, lint, type, compile,
   protected-file, scope, privacy, generated, and binary checks and publish
   the matching V02 Codex log ending `AWAITING_AUDIT`.

No schema, dependency, lock, UI, engine installation/execution, model,
metric-calibration, PL-0171+, physical/native, or tracker work is authorized.

## Final conclusion

`CHANGES_REQUIRED`. PL-0170 is not independently accepted. The task remains
open until the bounded V02 remediation is implemented, logged, and freshly
audited.
