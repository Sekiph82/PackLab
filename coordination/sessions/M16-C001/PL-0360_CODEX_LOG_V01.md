# PL-0360 - Codex Execution Log V01

Task: **Prevent Apple signing material in public repo**
Milestone: **M16 - CI/CD, Signing & Distribution**
Cycle: **M16-C001**

## Commits and synchronization

- Starting commit: `d823289f6dc346351dc7c5e7a1669b824aa7f4b0`.
- Implementation/evidence commits: `77c5a847453c9050af28fee81065f0c40d63b1e7`,
  `7262be2883b7b685493f2fcda4ce075c950eb599`, and
  `a34704a2e0a9098b2748a0d4734e5fea2815c9ee`.
- Tracker commit: `6c6884c8e16d1b53671c72881107e03e32875e06`.
- Final task-publication SHA: `6c6884c8e16d1b53671c72881107e03e32875e06`;
  `git ls-remote origin refs/heads/main` returned the same SHA.
- Origin was `https://github.com/Sekiph82/PackLab.git`; the task worktree
  began equal to `origin/main` and was fast-forward-free. Implementation,
  evidence and tracker changes were pushed directly to `main` as authorized.
- Owner Desktop synchronization and task-worktree cleanup are pending this
  log-only publication; they will be recorded in a follow-up log-only commit.

## Prompt and criteria

Read and followed:

- `coordination/sessions/M16-C001/PL-0360_CODEX_PROMPT_V01.md`
- `coordination/sessions/M16-C001/PL-0360_CHATGPT_AUDIT_CRITERIA_V01.md`
- `coordination/sessions/M16-C001/PL-0359_CODEX_PROMPT_V01.md` and its
  matching audit criteria
- M15 final audit, dependency/license register, versioning policy, secrets
  policy, live `TASKS.md`, and autonomous execution policies

No mandatory pre-read conflict was identified. No dependency, app runtime,
signing integration, M17 implementation, or Xcode/build configuration was
added.

## Changes

- Extended `tools/ci/ci_data_safety.py` to block `.cer`, `.p8`, `.p12`, `.pfx`,
  `.mobileprovision`, `.provisionprofile`, `.keychain`, and `.keychain-db`;
  scan PEM/private-key headers; and detect common direct signing-secret
  assignments, including base64 certificate/profile exports.
- Added a JSON documentation-marker allowlist. Suppression requires an exact
  Markdown path and line-ending-canonical SHA-256 to match both that manifest
  and a two-entry scanner source pin. The exception only permits inline prose
  markers without an END marker or long base64-like tail; it cannot suppress
  signing-material filenames or secret assignments. The two pinned files are
  historical public audit prose and contain no key bytes.
- Scanner diagnostics contain finding codes only. The scanner uses a resolved
  path for repository-relative identity while retaining symlink checks on the
  supplied path, covering Windows path-case aliases.
- Added `.gitignore` coverage, updated `docs/security/SECRETS_POLICY.md`,
  added a dedicated read-only GitHub signing guard for all pull requests and
  `main` pushes, and enabled the signing scan in Windows Python quality.
- Corrected a pre-existing Ruff `UP012` style error in
  `tests/tools/test_offline_version_inventory.py` by removing a redundant
  UTF-8 encoding argument; test semantics are unchanged.

## Validation

Focused/local commands and results:

| Command | Expected result / failure condition | Actual result |
| --- | --- | --- |
| `python -m unittest tests.tools.test_ci_signing_data_safety -v` | All signing-material, redaction, boundary and Windows alias cases pass; any mismatch fails the command. | **PASS**, 16/16 on Windows. |
| `python -m tools.ci.ci_data_safety --repository . --check-signing-secrets` | Current tracked source passes; any protected extension, private-key block or direct secret assignment blocks with codes only. | **PASS**. |
| `python -m tools.ci.ci_data_safety --repository . --tracked --check-workflows --check-environment --check-signing-secrets` | Full current tracked-data, workflow, environment and signing guard passes; any finding blocks. | **PASS**. |
| `uv run --locked ruff check core apps tools tests` | Repository Python lint passes; any lint finding fails. | **PASS**, `All checks passed!`. |
| `uv run --locked ruff format --check --config "format.line-ending = 'auto'" tools/ci/ci_data_safety.py tests/tools/test_ci_signing_data_safety.py tests/tools/test_offline_version_inventory.py` | All three changed Python files already formatted. | **PASS**. |
| `git diff --check` | No whitespace errors. | **PASS**. |
| `git ls-files '*.cer' '*.p8' '*.p12' '*.pfx' '*.mobileprovision' '*.provisionprofile' '*.keychain' '*.keychain-db'` | No tracked signing-material container. | No matching tracked paths. |

Hosted evidence:

- Dedicated signing-material guard: [run 41760545827](https://github.com/Sekiph82/PackLab/actions/runs/41760545827)
  on final implementation SHA `a34704a2e0a9098b2748a0d4734e5fea2815c9ee` —
  **success**. Runner label: `ubuntu-latest`; setup Python 3.12.15.
- Windows Python quality: [run 41760545803](https://github.com/Sekiph82/PackLab/actions/runs/41760545803)
  on the same SHA — guard, lock validation, Ruff, changed-file formatting
  and mypy passed. Full test step ended **4 failed, 2,261 passed, 10 skipped,
  1 deselected**. Runner label: `windows-latest`; Python 3.12.10.
- The four remaining full-suite failures are outside PL-0360's guard:
  `test_every_status_overridden_artifact_upload_has_an_explicit_guard_success_gate`,
  `test_optional_missing_file_uploads_still_require_an_immediately_preceding_guard`
  in `tests/ci/test_artifact_upload_guard_conditions.py`;
  `test_runtime_manifest_contract_excludes_owner_local_paths` in
  `tests/ci/test_owner_dev_launcher_contract.py`; and
  `test_accepted_note_must_match_cited_source_and_audit` in
  `tests/tools/test_offline_changelog.py`. The two artifact-upload findings
  are queued for PL-0361 triage. The OwnerDev and offline changelog failures
  remain distinct follow-up findings. PL-0360's own focused tests and dedicated
  hosted guard pass.
- Earlier hosted defects were fixed and retained in history: run 41759375720
  exposed CRLF/LF digest drift, fixed by canonical Markdown hashing; run
  41759375789 exposed the Windows path alias issue plus an existing Ruff
  violation. Run 41759917864 then verified the hash fix but still exposed the
  path alias and the four independent suite failures. Final run 41760545827
  passed the dedicated guard, and the final Windows run included all 16
  passing PL-0360 tests.

## Independent peer review and safety

- Source/workflow reviewer: **PASS** after inspection of the final source and
  workflow changes.
- Tester: **PASS**, 16/16 focused tests, both local guard commands, full-repo
  Ruff and diff check.
- Security reviewer: **PASS**, including the source-pinned documentation
  exception, redacted diagnostics, secret-free fixtures and repository path
  boundary.
- Evidence is in `PL-0360_CODEX_PEER_REVIEW_V01.md`. No historic ChatGPT audit
  verdict was created or claimed.
- No credentials, certificates, profiles, private keys, keychains, private
  scans, supplier data, personal data, or proprietary artwork were read into
  or added to source/evidence. No signing-secret values were read, created or
  logged. Test canaries are synthetic.
- No Xcode, simulator, signing, physical-device or release operation was run.
  There is no signed IPA acceptance or release approval.

## Handoff

PL-0360 is recorded `AUTO_AUDITED_PASS` in root `TASKS.md`. PL-0358 remains
`EXTERNAL_PENDING_APPLE_SIGNING_CREDENTIALS`. PL-0361 is now the active task.
The unresolved full-suite findings above remain visible and are not treated as
PL-0360 passes.

## Post-publication sync and worktree cleanup

- `tools/dev/post_task_safe_sync.ps1` was invoked against the canonical
  Desktop checkout. The helper did not return after approximately 20 seconds;
  only the exact PowerShell processes launched for that invocation
  were stopped. A separate status check found 74 tracked/untracked entries in
  the Desktop checkout (`main`, HEAD
  `f8745047063aca6c17378ecb33604e6e1e5b5f02`) while `origin/main` was
  `8f5bbebd77f02d7b774ac78cceede96d6f50be7a`. Owner changes were preserved;
  no fast-forward or parity claim was made. State: `LOCAL_SYNC_PENDING`.
- OwnerDev refresh was not run; PL-0360 does not change the native Windows app
  runtime or deployment.
- From the Desktop checkout, `git worktree list --porcelain` identified the
  exact task worktree
  `C:\Users\sekip\.codex\worktrees\pl0360-signing-material-guard\PackLab`.
  Before removal it was clean, at pushed SHA
  `8f5bbebd77f02d7b774ac78cceede96d6f50be7a`, equal to the verified
  `origin/main` SHA. No reparse points or active task processes were present.
  The 18,917 ignored paths were generated `.venv`, Ruff, package metadata and
  Python test caches from this task; no owner or protected data was present.
- Removed the worktree with normal `git worktree remove` (no force). The path
  no longer exists and the worktree registry has no matching entry.
- Actual C: free bytes immediately before removal: `211339935744`; after:
  `211382513664`; recovered: `42577920` bytes.
- This cleanup addendum is being published as a distinct PL-0360 log-only
  follow-up commit from the PL-0361 worktree. The task worktree was not deleted
  concurrently with implementation, validation, evidence, or publication.

READY_FOR_INDEPENDENT_AUDIT
