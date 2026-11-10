---
coordinationSchema: packlab-coordination/v1
artifactType: codex-log
cycleId: M17-C001
version: 01
actor: CODEX
status: LOCAL_COMPLETE_AUTONOMOUS_QUEUE_ARMED
promptPath: coordination/sessions/M17-C001/PL-0382_CODEX_PROMPT_V01.md
criteriaPath: coordination/sessions/M17-C001/PL-0382_VALIDATION_CRITERIA_V01.md
startingCommit: f8745047063aca6c17378ecb33604e6e1e5b5f02
finalCommit: f8745047063aca6c17378ecb33604e6e1e5b5f02
---

# PL-0382 Codex Log V01 — Crash/restart recovery

## Inputs and synchronization

- Read PL-0382 prompt/criteria, Studio `ProjectManager` authority/recovery code, and `tests/studio/test_project_revision.py`, `test_project.py`, `test_recovery.py`.
- HEAD `f8745047063aca6c17378ecb33604e6e1e5b5f02`, fetched `origin/main` `db772e35f386fcba88fa6dbdd01d186959fa7162`, 95 commits behind with dirty owner changes; no publish/refresh.

## Work and files

- Added a deterministic interruption hook test simulating a crash after the new authority record is durable but before compatibility mirrors update. Reopening repairs mirrors from authoritative bytes and retains raw capture bytes.
- Existing tests cover malformed/future schema byte preservation and recovery checkpoint digest mismatch.
- File: `tests/studio/test_project_revision.py`, `tests/studio/test_project.py`, `tests/studio/test_recovery.py`.

## Validation / limitations

- Expected: the atomically published authority record is restored and stale mirrors are repaired; separately SHA-256-bound recovery checkpoints are rejected if their source bytes changed. Source capture remains unchanged. Assertions are present in test source.
- M17 pytest/Tester **NOT RUN**; no runtime pass claimed. No live application was killed or owner project touched.
- No secrets/private data committed; no commit/push/Desktop sync because checkout remains dirty/divergent.

## Independent source-review qualification

- The authority record is atomically written and fsynced, but does not contain an embedded checksum. The SHA-256 binding applies to recovery checkpoints, not to the authority file itself.
- This source evidence simulates an interruption after authority publication and before mirror updates. It does not simulate process termination or power loss.

**LOCAL_COMPLETE_AUTONOMOUS_QUEUE_ARMED** — crash/restart test source is prepared for grouped M17 execution; task remains unchecked until validation/review.
