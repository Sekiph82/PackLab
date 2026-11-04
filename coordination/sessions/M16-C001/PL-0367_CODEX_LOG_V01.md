# PL-0367 Codex Execution Log V01

Task: **Rollback for incompatible Capture/Studio versions**  
Milestone: **M16 - CI/CD, Signing & Distribution**  
Cycle: **M16-C001**

## Synchronization and authority

- Canonical repository: `Sekiph82/PackLab`, branch `main`; origin URL verified as `https://github.com/Sekiph82/PackLab.git`.
- Starting task SHA: `affb381e934ec6ccf9e352c94b64d10931fd4ffd`, fetched from `origin/main` before implementation.
- Implementation SHA: `ffa78546d02b7d7e8be3a266708098a492dd8ad0`.
- GitHub `main` was at `ffa78546d02b7d7e8be3a266708098a492dd8ad0` after the implementation/evidence push. Tracker and this log are published in subsequent commits.
- Read the active PL-0367 prompt and criteria, M15 final audit, versioning policy, dependency/license register, relevant PL-0362 through PL-0366 contracts/logs, current version sources, Packaging Library backup service, and the offline install/rollback preparation guide.

## Changes

- Added `docs/packaging/PL0367_ROLLBACK_PLAYBOOK.md`, a deterministic procedure for manifest/provenance-bound artifact selection, schema decisions, unsupported downgrade/migration stops, project/library/package preservation, Windows Studio rollback, Capture reinstall constraints, and exact build-identity verification.
- Updated `docs/packaging/PL0362_PL0367_OFFLINE_INSTALL_ROLLBACK_PREPARATION.md` to reference the detailed playbook and reflect current migration/device limits.
- Added a regression case in `tests/tools/test_offline_release_manifest.py` confirming an unimplemented schema migration claim is rejected.
- Added `coordination/sessions/M16-C001/PL-0367_CODEX_PEER_REVIEW_V01.md` with attributed source, test, and security reviewer findings.
- Updated root `TASKS.md` to record the verified PL-0367 result and advance the queue to PL-0369.
- No runtime dependency, release artifact, credential, signing material, private scan, supplier file, or Kenya dataset was added.

## Version and provenance facts

Command: `uv run --locked python tools/release/offline_version_inventory.py --repo . --commit ffa78546d02b7d7e8be3a266708098a492dd8ad0`

Expected: inventory binds exact source and independent version domains, rejects source mismatch, and makes no artifact/release assertion. Actual: exit 0; source SHA matched. Studio `0.1.0`; Capture `0.1.0`, build `1`, bundle `com.packlab.capture`; PackScan schema `1.0.0`; release-train ID `packlab-rt-v1-f62817d1f1dd3d877376e870c6c2d076f3bbe9e478b527e667f29dd4e038783e`; status `OFFLINE_UNVERIFIED_BUILD`; artifact digest `null`; hosted build `false`; legal review `PENDING`; factory release `NOT_AUTHORIZED`.

## Validation and acceptance evidence

- `uv run --locked pytest -q tests/tools/test_offline_release_manifest.py -k "source_versions_compatibility_toolchain_and_m17 or rollback_manifest_rejects_unimplemented_schema_migrations"` — **2 passed, 11 deselected**. Expected: supported current declaration is recognized and unsupported migration claims fail closed. Failure condition: a migration claim is accepted or current compatibility declaration fails.
- `uv run --locked python tools/ci/ci_data_safety.py --repository . --check-signing-secrets` — `PACKLAB_CI_DATA_GUARD=PASS`; expected: no private data, signing material, or unsafe tracked payload. Failure condition: guard reports any finding.
- `git diff --check` — passed after final edits.
- Tester peer review additionally reported Ruff lint/format and release-manifest schema JSON parsing passed. This evidence is scoped to the task and is not a separate milestone regression claim.
- The owner-authorized push at the M16/M17 boundary triggered the complete hosted Windows Python Quality workflow. Hosted [run 41789020962](https://github.com/Sekiph82/PackLab/actions/runs/41789020962) passed at exact implementation SHA `ffa78546d02b7d7e8be3a266708098a492dd8ad0`: **2,312 passed, 10 skipped, 1 deselected, 2 warnings**; lock validation, Ruff, format, mypy, and the full unit/repository suite passed.
- Hosted [Signing Material Guard run 41789021137](https://github.com/Sekiph82/PackLab/actions/runs/41789021137) passed at the same SHA.
- Independent source review PASS after re-reading the final playbook and correcting the policy-evidence wording. Test review PASS. Security review PASS after clarifying private `.packscan` names/hashes stay in owner records. Full attributed findings are in the peer-review record.

## Privacy, limitations, and failure handling

The playbook does not mutate raw `.packscan` data, infer compatibility from version-number proximity, or permit an unimplemented migration/downgrade. Private package names and hashes remain in owner records; public repository notes are limited to public source/build/manifest digests and sanitized decision codes. The signing-secret/data guard passed.

No production manifest, exact previous rollback artifact, signed IPA, Capture in-app restore path, physical iPhone acceptance, authenticated legal approval, or release authorization is established. No M17 implementation or PL-0368 release work was pulled forward. There were no failing checks or unresolved correctable review findings.

## Publication and synchronization

Implementation and peer-review evidence were committed as `ffa78546d02b7d7e8be3a266708098a492dd8ad0` and pushed to `origin/main`; remote SHA was verified equal. This execution log is published separately as a log-only commit. The owner Desktop checkout is an existing dirty checkout; the safe sync helper will be run after final publication and its actual result recorded. No OwnerDev refresh is relevant to this documentation/tooling task.

## Worktree lifecycle

Task worktree: `C:\Users\sekip\.codex\worktrees\pl0367-release-rollback\PackLab`, branch `codex/pl0367-release-rollback`. This worktree remains intact until this log and publication finish. Afterward, inspect cleanliness, ignored contents, processes/reparse points, and owner data from a stable checkout outside the target; remove only with normal `git worktree remove` if safe. Record actual C: free bytes before/after. If removal is not demonstrably safe, preserve it and report `WORKTREE_CLEANUP_BLOCKED`. Any cleanup follow-up will preserve the exact final status line below.

## Handoff

PL-0367 is complete under Codex's owner-authorized peer-review policy. The M16 release-preparation scope is complete; PL-0368 remains deferred until its M17 gates. The dependency-ready queue advances to PL-0369.

READY_FOR_INDEPENDENT_AUDIT
