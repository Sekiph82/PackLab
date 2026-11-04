# PL-0361 - Codex Execution Log V01

Task: **Publish build artifacts with clear signed/unsigned provenance**  
Milestone: **M16 - CI/CD, Signing & Distribution**  
Cycle: **M16-C001**

## Commits and synchronization

- Starting commit: `085a610e56b31f8f6242b8fd728834be3be2e865`.
- Implementation commit: `f977eb7f3d0a6fee1ff0bd474f5b1557457a590a`.
- Peer-review and tracker commit: `22f0a86cf0ccd2ab3d2da4034afe114367fe2f93`.
- Final task-publication SHA before this log-only commit:
  `22f0a86cf0ccd2ab3d2da4034afe114367fe2f93`.
- Origin is `https://github.com/Sekiph82/PackLab.git`. Starting checkout was
  equal to `origin/main`; both commits were pushed directly to `main` under the
  owner's authorization. Remote SHA verification is recorded after publication.
- Desktop safe synchronization and task-worktree cleanup are pending this
  log-only publication and will be recorded in a log-only follow-up commit.

## Prompt and criteria

Read and followed:

- `coordination/sessions/M16-C001/PL-0361_CODEX_PROMPT_V01.md`
- `coordination/sessions/M16-C001/PL-0361_CHATGPT_AUDIT_CRITERIA_V01.md`
- `coordination/sessions/M16-C001/PL-0360_CODEX_PROMPT_V01.md` and its
  matching criteria
- Live `TASKS.md`, M15 final audit, dependency/license register, versioning
  policy, secrets policy, and autonomous execution policies

The relevant dependency and secret boundaries were consistent with the active
prompt. No Apple signing credential, certificate, profile, private key,
keychain, signing integration, runtime cloud feature, new dependency, or M17+
implementation was added. PL-0358 remains externally pending owner-provided
Apple signing credentials; the helper deliberately rejects signed IPA records
until a real signed artifact path can validate the signature and profile.

## Changes

- Added `tools/ci/ios_artifact_provenance.py`, a standard-library-only
  prepare/verify utility that emits strict JSON metadata for unsigned
  simulator apps and generic iOS archives. It binds sorted relative paths,
  file lengths and contents with a deterministic SHA-256 tree digest and
  reports aggregate uncompressed byte length and file count.
- The sidecar records artifact/signing type, Capture version/build, PackScan
  schema, source SHA, Xcode and SDK versions, bundle identifier, pinned
  `Package.resolved` digest, repository/workflow/run identity, product digest,
  byte length and file count. Unknown fields, invalid values, signing-state
  mismatch, unsupported `ios_signed_ipa`, symlinks, junctions, empty products,
  and sidecar digest/length/count mismatches fail closed with value-redacted
  diagnostics.
- Replaced legacy simulator/archive text manifests with JSON sidecars and
  immediate verification steps before each product upload. Artifact names
  retain explicit `unsigned-simulator` and `unsigned-device-archive` labels;
  one-day retention and `contents: read` permissions remain.
- Added a bounded guard before failed XCTest diagnostics upload. The guard
  requires a runner-temp result bundle, rejects links, and caps it at 1 GiB.
  Missing diagnostics now fail closed. SPM resolution evidence only uploads on
  success and requires the validated `Package.resolved` file.
- Included the provenance helper in macOS workflow pull-request and `main`
  push path filters. Added negative/boundary and workflow contract tests.
- Repaired the three remaining Windows full-suite failures: status-overridden
  artifact upload expectations, OwnerDev runtime-manifest scope, and offline
  changelog path canonicalization.

## Local validation

| Command | Expected result / failure condition | Actual result |
| --- | --- | --- |
| `uv sync --locked --all-groups` | Install the locked project/test environment without changing lockfiles. | **PASS**; dependencies resolved from the checked-in lock. |
| `uv run --locked pytest -q tests/ci/test_ios_artifact_provenance.py tests/ci/test_artifact_upload_guard_conditions.py tests/ci/test_owner_dev_launcher_contract.py tests/tools/test_offline_changelog.py` | Provenance, upload gating, OwnerDev scope and offline path tests pass; any mismatch fails. | **PASS**, 33 passed, 1 skipped because this Windows environment did not permit symlink creation. Junction rejection was exercised by a controlled test double. |
| `uv run --locked pytest -q` | Full repository suite passes; any failed test or collection error fails. | **PASS**, 2,272 passed, 13 skipped, 1 deselected. Two existing duplicate-ZIP-name warnings were emitted by negative tests. |
| `uv run --locked ruff check core apps tools tests` | Repository lint passes; any finding fails. | **PASS**, `All checks passed!`. |
| `uv run --locked ruff format --check --config "format.line-ending = 'auto'" -- tools/ci/ios_artifact_provenance.py tests/ci/test_ios_artifact_provenance.py tests/ci/test_artifact_upload_guard_conditions.py tests/ci/test_owner_dev_launcher_contract.py tools/release/offline_changelog.py` | All changed Python files are formatted. | **PASS**, 5 files already formatted. |
| `git diff --check` | No whitespace errors. | **PASS**. |

Environment setup failures were corrected and are not test passes: the first
system-Python full-suite attempt could not import the installed PackLab package;
the first default `uv run pytest` collection lacked PyYAML. Installing all
locked groups with `uv sync --locked --all-groups` resolved both. The system
Ruff 0.11.11 did not match the project lock; the locked Ruff command passed.

## Hosted evidence

- **PackLab Capture macOS CI:** [run 41764141005](https://github.com/Sekiph82/PackLab/actions/runs/41764141005), exact source
  `f977eb7f3d0a6fee1ff0bd474f5b1557457a590a` — **success**. Runner:
  `macos-15`, macOS 15.8.2, Xcode 16.0 build 16A242d, iOS SDK 18.0 and
  iPhone 16 / iOS 18.0 simulator. Full XCTest summary: **205 passed, 0 failed,
  0 skipped**.
- Unsigned simulator product tree verification passed immediately before
  upload: SHA-256
  `93639751561f7bff2e338247a160821221ffa3270afa4f7e3f2788d17ba48bde`,
  8,178,129 bytes. Artifact `13292221930`, 2,228,803 compressed bytes,
  artifact digest `sha256:912746cab418aadd60fdd452cd45069507dbc2cbf22f4bb67fc6e2c31063bb64`,
  expires `2026-11-05T03:06:38Z`.
- Unsigned device archive product tree verification passed immediately before
  upload: SHA-256
  `eb91d6b73ddd8e74163c3168636cb7eafbf9f659994bf385ac383eaec9880fa2`,
  20,800,973 bytes. Artifact `13291404205`, 5,380,642 compressed bytes,
  artifact digest `sha256:bea54dad45dddd58107a0199e48c065d95f7e3aef090421baf7f4c496dd901d4`,
  expires `2026-11-05T03:00:07Z`. Archive checks established the app was
  unsigned and contained no provisioning profile or `_CodeSignature`; it is
  not an installable IPA.
- **PackLab Windows Python Quality:** [run 41764141048](https://github.com/Sekiph82/PackLab/actions/runs/41764141048), same SHA —
  **success**. Locked Ruff, changed-file formatting, mypy, and repository
  tests passed: 2,276 passed, 10 skipped, 1 deselected, 2 expected
  duplicate-ZIP-name warnings.
- **PackLab Signing Material Guard:** [run 41764141180](https://github.com/Sekiph82/PackLab/actions/runs/41764141180), same SHA —
  **success**.
- PL-0354's previously missing full hosted macOS validation was already
  complete on the canonical tracker. I verified [run 41743543561](https://github.com/Sekiph82/PackLab/actions/runs/41743543561)
  reports success for the unsigned iPhone 16 / iOS 18.0 simulator and
  205/205 XCTest. Its exact source was
  `3cc10fe5241d95f2dce7fb909e15b129342d37a3`.

## Independent peer review and safety

- Source/workflow reviewer: **PASS** after inspecting the actual source,
  workflow, tests and hosted run.
- Tester: **PASS**; the focused contract suite, repository test suite, lint
  and hosted Windows/macOS results are recorded above.
- Security reviewer: **PASS**; strict sidecar field allowlist, path/link
  boundaries, workflow permissions, pinned actions, retention and secret
  handling were inspected.
- Review evidence: `PL-0361_CODEX_PEER_REVIEW_V01.md`. No independent
  ChatGPT audit file or audit verdict was created or claimed.
- No secrets, personal identifiers, private scans, supplier files or
  proprietary artwork were read or added. No credential values were logged.
- No signed IPA, physical iPhone installation, signing acceptance, legal
  approval, or release readiness is claimed.

## Handoff

PL-0361 is recorded in `TASKS.md` as
`CODEX_IMPLEMENTATION_PASS / READY_FOR_INDEPENDENT_AUDIT`. PL-0362 is active.
PL-0358 remains `EXTERNAL_PENDING_APPLE_SIGNING_CREDENTIALS`.

## Post-publication synchronization and worktree cleanup

- `tools/dev/post_task_safe_sync.ps1` was invoked against the Desktop checkout
  after publication but did not return within approximately 15 seconds; the
  invocation was interrupted. A direct read-only fetch/status check confirmed
  Desktop `main` remains at `f8745047063aca6c17378ecb33604e6e1e5b5f02`,
  `origin/main` is `f977eb7f3d0a6fee1ff0bd474f5b1557457a590a`, and 74 dirty
  entries remain. No Desktop files were changed. State: `LOCAL_SYNC_PENDING`.
- OwnerDev refresh was not relevant; this task changed no Windows runtime or
  deployment.
- The PL-0361 worktree cleanup is pending the publication of this log. Record
  its exact safety checks and actual C: free-byte change in a log-only
  follow-up commit after cleanup. Do not remove or alter the dirty Desktop
  checkout or its owner work.

READY_FOR_INDEPENDENT_AUDIT
