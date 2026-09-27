---
coordinationSchema: packlab-coordination/v1
artifactType: chatgpt-audit
cycleId: M07-C001
taskId: PL-0174
version: V02
actor: CHATGPT
verdict: CHANGES_REQUIRED
promptPath: coordination/sessions/M07-C001/PL-0174_CODEX_PROMPT_V02.md
criteriaPath: coordination/sessions/M07-C001/PL-0174_CHATGPT_AUDIT_CRITERIA_V02.md
codexLogPath: coordination/sessions/M07-C001/PL-0174_CODEX_LOG_V02.md
auditedBase: e6c44276e1e7206921426ac8afa062a95f3b6fbf
implementationCommit: 6bc57fadced0e667267e75c40cfa8ac1d6d634a5
auditedHead: 80f740dc092bde104f30891fdf4f803d0fb179ac
---

# PackLab ChatGPT Audit V02 - PL-0174

## Verdict

`CHANGES_REQUIRED`

The V02 implementation is narrowly scoped and its recorded runtime/static
checks are reproducible, but two public-boundary contract defects remain:

1. A COLMAP camera record with a non-positive focal parameter is accepted,
   although the accepted `SparseExportCamera` contract requires focal
   parameters to be positive.
2. A valid accepted sparse export with an image containing zero 2D
   observations is rejected because `_data_lines` removes the meaningful
   blank observation line before image-pair parsing.

PL-0174 remains open. A bounded V03 remediation is required before closure.

## Scope audited

- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`
- Live tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CODEX_PROMPT_V02.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CHATGPT_AUDIT_CRITERIA_V02.md
- Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CODEX_LOG_V02.md
- Audited base: `e6c44276e1e7206921426ac8afa062a95f3b6fbf`
- Implementation commit: `6bc57fadced0e667267e75c40cfa8ac1d6d634a5`
- Log-only/audited head: `80f740dc092bde104f30891fdf4f803d0fb179ac`
- Implementation diff: https://github.com/Sekiph82/PackLab/compare/e6c44276e1e7206921426ac8afa062a95f3b6fbf...6bc57fadced0e667267e75c40cfa8ac1d6d634a5
- Full audited range: https://github.com/Sekiph82/PackLab/compare/e6c44276e1e7206921426ac8afa062a95f3b6fbf...80f740dc092bde104f30891fdf4f803d0fb179ac

## Evidence classification

### E1/E2 Codex evidence

- The V02 log records the required separate implementation/log publication,
  exact commands, limitations, commit identities, remote visibility, and
  `AWAITING_AUDIT` handoff.

### E3 independent ChatGPT evidence

- Verified the canonical checkout, `main` branch, expected `origin`, clean
  status, `HEAD == origin/main`, and `0 0` divergence after
  `git fetch origin main --prune`.
- Inspected the live tracker, V02 prompt/criteria/log, V01 audit, the actual
  implementation and test diffs, accepted sparse-export source/tests, the
  PL-0163 reconstruction contract, the M07 engine baseline, and the OpenReality
  architecture.
- Independently reran the focused boundary/regression suite: `227 passed`.
- Independently reran `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked
  pytest -q -rs`: `539 passed, 5 skipped, 1 deselected, 2 warnings`.
  The skips are four unavailable `cv2` checks and one Windows symlink-
  privilege limitation (`WinError 1314`); warnings are unchanged duplicate-ZIP
  fixture warnings.
- Independently reran Ruff check/format, targeted mypy, compileall,
  `git diff --check`, protected tracker/scope checks, and remote SHA checks.
  Repository-wide mypy independently reproduced the unchanged 18 errors in
  five files; the changed implementation path remains clean.
- Independently called the public conversion function with a malformed
  `PINHOLE` record whose first focal parameter was `0`; it was accepted.
- Independently built a valid accepted sparse-export bundle with two images and
  empty observation lists; conversion rejected it as malformed observations.

### E4 owner evidence/decision

None required for this software-boundary correction. No physical, native-device,
account, clean-machine, or owner-only acceptance is claimed.

## Criteria matrix

| # | Result | Evidence / finding |
|---:|---|---|
| 1 | PASS | Live `TASKS.md` authorized M07-C001 / PL-0174 / `CHANGES_REQUIRED` / `CODEX`; PL-0173 remains `AUDITED_PASS`, PL-0068 remains `OWNER_REQUIRED`, and PL-0175+ remains unauthorized. |
| 2 | PASS | The implementation commit changes only `openmvs_conversion.py` and its public-boundary test; the log is separate and accepted PL-0166 through PL-0173 files are untouched. |
| 3 | CHANGES_REQUIRED | The parser rejects the listed unsupported models, cardinality, dimensions, and non-finite values, but accepts a non-positive focal parameter required to be positive by `SparseExportCamera`. |
| 4 | PASS | The public boundary rejects the V01 image findings, unsafe/duplicate names, invalid pose/camera fields, malformed observations, and non-finite coordinates while retaining camera/point/track consistency checks. |
| 5 | PASS | Invalid RGB/error/XYZ values, empty tracks, malformed track IDs, duplicate records, and exact observation/track mismatches are rejected. |
| 6 | CHANGES_REQUIRED | The immutable plan, provenance, canonical digest, pins, limitations, and no-execution boundary remain intact, but the record parser both accepts invalid focal values and rejects a valid empty-observation export. |
| 7 | CHANGES_REQUIRED | V02 tests cover the V01 findings and most new malformed boundaries, but do not cover non-positive focal rejection or valid empty-observation acceptance; the latter is an accepted sparse-export regression. |
| 8 | PASS | The exact locked full suite exits 0 with only the disclosed unavailable-capability/Windows skips and unchanged warnings. |
| 9 | PASS | Independent static, compile, diff, protected-file, scope, dependency/lock, privacy, generated/binary, and remote checks are clean; unchanged repository-wide mypy debt is disclosed. |
| 10 | PASS | `PL-0174_CODEX_LOG_V02.md` is remotely visible, uses full GitHub URLs, records separate publication boundaries, and ends exactly `AWAITING_AUDIT`. |
| 11 | PASS | No engine execution/discovery, `.mvs` writer, later stage, schema/dependency/lock, tracker/audit edit by Codex, native/physical acceptance, or PL-0175+ implementation was found. |

## Findings

### High

- `core/src/packlab_core/openmvs_conversion.py` validates camera parameter
  finiteness and cardinality but does not apply the accepted model-specific
  positive focal-parameter rule from `SparseExportCamera.__post_init__`. The
  public conversion boundary therefore accepts a malformed camera artifact.
- `_data_lines` removes blank lines globally. Since the accepted exporter emits
  an empty second line for an image with zero observations, the public parser
  cannot consume every valid `SparseExportBundle` produced by the accepted
  sparse-export contract.

## Architecture / regression / security review

- Architecture: the PackLab-owned, non-executing conversion-plan boundary and
  OpenMVS authority limitations remain sound; the defects are confined to
  artifact-record validation and valid-bundle compatibility.
- Regression: the focused and full suites are green, but they do not exercise
  the two cases above.
- Test sensitivity: direct public-boundary probes demonstrate both false
  acceptance of invalid camera data and false rejection of valid exporter data.
- Security/privacy: no credentials, signing material, private scans, supplier
  files, binaries, generated reconstruction intermediates, or private paths
  were added.
- Scope leakage: none found; the implementation range is exactly the two
  authorized product/test paths and the separate V02 log.

## Reusable audit learnings

- NONE; this audit records task-local PL-0174 parser corrections.

## TASKS.md action

PL-0174 remains unchecked and `CHANGES_REQUIRED`. ChatGPT publishes the bounded
V03 prompt and criteria, keeps `Required Actor: CODEX`, preserves PL-0173 as
`AUDITED_PASS`, keeps PL-0068 as `OWNER_REQUIRED`, and leaves PL-0175+ closed to
execution.

## Remediation

V03 must only:

1. enforce the accepted model-specific positive focal-parameter rule at the
   public camera parser and add a public regression for non-positive focal data;
2. preserve meaningful empty observation lines while parsing image header/
   observation pairs, so valid zero-observation exports are accepted without
   weakening malformed-record, count, reference, or track checks; and
3. add public-boundary regression coverage for both cases while retaining all
   V02 malformed-record and accepted predecessor coverage.

No execution, discovery, later OpenMVS stage, schema/dependency/lock, UI,
filesystem, or PL-0175+ work is authorized.

## Final conclusion

PL-0174 V02 is `CHANGES_REQUIRED`. Codex must execute the published V03
remediation, write `PL-0174_CODEX_LOG_V03.md`, and return `AWAITING_AUDIT` for a
fresh independent audit.
