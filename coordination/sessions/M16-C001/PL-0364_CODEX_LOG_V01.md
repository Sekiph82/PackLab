# PL-0364 - Codex Execution Log V01

Task: **Add release manifest with dependency versions and schema compatibility**  
Cycle: **M16-C001**  
Prompt: `coordination/sessions/M16-C001/PL-0364_CODEX_PROMPT_V01.md`  
Criteria: `coordination/sessions/M16-C001/PL-0364_CHATGPT_AUDIT_CRITERIA_V01.md`

## Source and synchronization

- Stable starting commit before implementation: `c1434b07ea5707d1ca96af6afcaa94266b557f2c`.
- Implementation commit: `7139f0de042ada7ef6b393fdbcaea390c7e03bd5`.
- Tracker and peer-review evidence commit: `ce5d42ba17d86d0c71a6c98a44dd8e24c2e5e85e`.
- This log-only commit: recorded by the commit that adds this file.
- Branch: task worktree `codex/pl0364-release-manifest`; publication target `origin/main`.
- Remote synchronization: implementation and evidence commits were pushed; remote `refs/heads/main` was checked and matched `ce5d42ba17d86d0c71a6c98a44dd8e24c2e5e` before this log publication. The log commit is pushed and verified separately.
- Desktop synchronization: `LOCAL_SYNC_PENDING`. The Desktop checkout has owner changes (previously observed 74 dirty entries) at local SHA `f8745047063aca6c17378ecb33604e6e1e5b5f02`; no files there were changed. The required safe-sync helper is being checked as part of task cleanup.

## Contract and implementation

Read the PL-0364 prompt and audit criteria, the M15 final audit, M16 offline release preparation and version policy, dependency/license register, predecessor task prompts/criteria/logs, and the current version/dependency/toolchain sources. The implementation preserves the distinct current domains: Studio `0.1.0`, Capture `0.1.0` build `1`, PackScan schema `1.0.0`.

Changed files:

- `tools/release/offline_release_manifest.py`
- `tests/tools/test_offline_release_manifest.py`
- `schemas/release/release-manifest.schema.json`
- `docs/packaging/PL0364_RELEASE_MANIFEST_CONTRACT.md`
- `docs/packaging/M16_OFFLINE_RELEASE_CONTROL_PREPARATION.md`
- `coordination/sessions/M16-C001/PL-0364_CODEX_PEER_REVIEW_V01.md`
- root `TASKS.md`
- this execution log

The tool builds deterministic preparation-only manifest content and rejects incomplete or inconsistent candidate evidence. It binds the exact source commit and independent version tuple; verifies relevant dependency and toolchain Git blobs against HEAD; validates Windows/iOS artifact provenance, artifact digests, byte lengths, build-run/source correspondence and signing state; checks schema compatibility; requires notice/inventory and explicit limitations; and restricts evidence paths to safe normalized repository-relative paths. Manifest identity excludes path and timestamp variation and binds content digests and facts. Output is fixed to `PREPARATION_ONLY_NOT_RELEASE_AUTHORIZATION`, `release_authorization: NOT_GRANTED`, and `m17_status: NOT_ACCEPTED`.

The exact source train inventory at implementation commit is
`packlab-rt-v1-bd8358001110a84a1e372ddfb8f817cd96a48192950d57656d19145d0316d8ed`,
and is still `OFFLINE_UNVERIFIED_BUILD`. No current production manifest was
emitted because a complete current-source Windows+iOS artifact set, matching
build receipts and complete distribution evidence were unavailable.

## Validation

Expected behavior: complete, mutually consistent evidence produces a stable preparation manifest; missing, malformed, mismatched, unsafe-path, tampered-source or invalid signing evidence fails closed without an output manifest. Any acceptance of untrusted facts, unsafe paths, mismatched source blobs, or release/M17 authorization would be a failure.

- Environment: `uv sync --locked --all-groups` completed in the task worktree; no lockfile or dependency manifest changed.
- Focused module: `uv run --locked pytest -q tests/tools/test_offline_release_manifest.py` — **10 passed, 1 skipped** at the run before the final isolated regression additions. The skip is the symlink-creation capability case unavailable on this Windows environment.
- Source-binding regression: `uv run --locked pytest -q tests/tools/test_offline_release_manifest.py -k test_dependency_and_toolchain_sources_are_bound_to_head_even_assume_unchanged` — **1 passed** after adding ordinary and `assume-unchanged` tampering for `Package.resolved` and OCCT contract evidence.
- CLI regression: `uv run --locked pytest -q tests/tools/test_offline_release_manifest.py -k script_cli_rejects_incomplete_candidate_without_writing_manifest` — **1 passed**; incomplete CLI input rejects and writes no output file.
- Final static checks after the last code/test changes: Ruff check passed; Ruff format check passed; mypy passed; `git diff --check` passed.
- These are separate runs and are not represented as one combined test count.
- Hosted Windows Python Quality [run 41779051439](https://github.com/Sekiph82/PackLab/actions/runs/41779051439) passed at implementation SHA `7139f0de042ada7ef6b393fdbcaea390c7e03bd5`: repository suite **2,288 passed, 10 skipped, 1 deselected, 2 warnings**; Ruff, format, and mypy passed.
- Hosted Signing Material Guard [run 41779051476](https://github.com/Sekiph82/PackLab/actions/runs/41779051476) passed at implementation SHA `7139f0de042ada7ef6b393fdbcaea390c7e03bd5`.
- Train inventory command: `uv run --locked python tools/release/offline_version_inventory.py --commit 7139f0de042ada7ef6b393fdbcaea390c7e03bd5` — returned the version tuple and train identity above with `OFFLINE_UNVERIFIED_BUILD`, no artifact digest, and no release authorization.

## Reviews and limitations

The source reviewer, tester and security reviewer inspected the implementation/tests/evidence and returned PASS; resolutions and scope boundaries are recorded in `coordination/sessions/M16-C001/PL-0364_CODEX_PEER_REVIEW_V01.md`. This is advisory implementation peer review, not an independent ChatGPT audit. CI receipt authenticity and cryptographic signature verification are not performed by this offline preparation tool.

No secrets, credentials, signing private material, private Kenya scans, confidential supplier data or new dependencies were added. No Apple signing, legal approval, physical-device acceptance, GitHub release, tag, production release, M17 acceptance or PL-0368 release approval is claimed. Desktop sync, task worktree cleanup and actual C: free-space before/after measurements remain to be recorded after safe cleanup checks.

## Handoff

`TASKS.md` now records PL-0364 as `CODEX_IMPLEMENTATION_PASS / READY_FOR_INDEPENDENT_AUDIT` and PL-0365 as the active next task, consistent with the owner-authorized Codex tracker delegation in current `AGENTS.md`. PL-0365's prompt contains a historical tracker-ownership line that conflicts with this current owner authorization; the tracker will continue to follow the current `AGENTS.md` contract.

READY_FOR_INDEPENDENT_AUDIT
