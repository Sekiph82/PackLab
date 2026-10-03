# M12-C001 - Remediation & Continuation Master Work Order V02

Milestone: **M12 - Advanced Packaging Geometry**
Remediation frontier: **global subprocess cancellation determinism**
Blocked child to revalidate: **PL-0269**
Remaining ordered children after closure: **PL-0270 through PL-0288**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

This remediation/continuation prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_REMEDIATION_CONTINUATION_CODEX_PROMPT_V02.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_REMEDIATION_CONTINUATION_CHATGPT_AUDIT_CRITERIA_V02.md

Remediation/continuation log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_REMEDIATION_CONTINUATION_CODEX_LOG_V02.md

Original M12 master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_CODEX_PROMPT_V01.md

Original M12 master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_CODEX_LOG_V01.md

PL-0269 independent audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0269_CHATGPT_AUDIT_V01.md

## Verified starting state

At the independent audit frontier:

- remote `main`: `8ec5b4c822d4b97d13eea125c64691971baf3b58`;
- PL-0268 implementation is independently `AUDITED_PASS`;
- PL-0269 implementation SHA is `c6f935fc0308256af528cc596ff01e55d3242763`;
- PL-0269 focused/static checks are green;
- PL-0269 did not modify reconstruction/process-runner code;
- locked full suite failed twice only at `test_stage_cancellation_is_distinct`;
- that test passes alone;
- PL-0270 through PL-0288 were not started;
- M13 was not started.

## Mandatory synchronization

Before any write:

1. `git fetch origin main --prune`
2. verify repository root and remote `Sekiph82/PackLab`
3. inspect `git status --porcelain`
4. inspect `git rev-list --left-right --count HEAD...origin/main`
5. preserve all owner-local work; no reset/clean/rebase/force-push
6. fast-forward only when safe and behind-only
7. verify live `TASKS.md` authorizes this M12 remediation/continuation and M13 remains unauthorized

Stop `TASK_STATE_MISMATCH` on conflict.

# Phase A - Fix deterministic pre-set cancellation

## Frozen maintenance scope

Primary authorized implementation files:

- `core/src/packlab_core/subprocess_runner.py`
- `tests/core/test_subprocess_runner.py`

Only if directly required by the public contract/regression:

- `core/src/packlab_core/reconstruction_process.py`
- `tests/core/test_reconstruction_process.py`

Do not modify PL-0269 implementation merely to make the unrelated suite failure disappear.

## Required semantic fix

A `cancel_event` that is already set when `run_process(...)` begins must be handled **deterministically before child execution can win the race**.

Preferred behavior:

- validate the command/options normally;
- if an explicitly supplied cancellation event is already set before spawn, do not spawn the child process at all;
- return a structured `ProcessResult` with:
  - the normalized command;
  - `returncode=None`;
  - empty stdout/stderr;
  - `timed_out=False`;
  - `cancelled=True`;
  - an explicit non-secret cancellation reason;
- callbacks must not run and child-side effects must not occur.

Preserve existing semantics for cancellation that occurs after a process has started, including owned process-tree termination/cleanup. Preserve timeout semantics.

Do not solve this by adding arbitrary sleep, test retries, xfail/skip, weakening assertions or making cancellation probabilistic.

## Required remediation regressions

Add/retain tests proving:

1. a pre-set event returns `cancelled=True`;
2. a pre-set event does not execute a child side effect, preferably by using a temp marker file the child would create;
3. `run_reconstruction_stage()` reports `StageStatus.CANCELLED` for the pre-set event and does not report `SUCCEEDED`;
4. live cancellation still stops the runner-owned process tree;
5. timeout behavior remains distinct from cancellation;
6. successful/nonzero process behavior remains unchanged.

Run the existing cancellation-distinct regression repeatedly, at least **20 sequential invocations**, without altering its assertions. Record exact pass count.

## Phase A validation

Run at minimum:

- direct subprocess-runner focused suite;
- reconstruction-process focused suite;
- relevant process-tree cancellation/timeout tests;
- changed-file Ruff;
- changed-file format check;
- targeted mypy;
- compileall;
- `git diff --check`;
- secrets/privacy/scope/dependency review.

Then run the exact locked full suite:

`uv run --locked pytest -q`

Require **two consecutive green full-suite runs** at the same final remediation code revision before closing the global determinism gate.

Publish the remediation implementation/evidence in a dedicated commit. Do not edit `TASKS.md`.

# Phase B - Revalidate and close PL-0269

Reuse the existing PL-0269 implementation at:

`c6f935fc0308256af528cc596ff01e55d3242763`

Do not rewrite it unless a direct PL-0269 test/source defect is independently demonstrated after the shared remediation.

Re-run:

- `tests/core/test_jerrycan_handle_void_candidates.py`
- `tests/core/test_cross_section_overlay.py`
- PL-0269 changed-file Ruff/format/mypy/compileall/diff/scope checks.

The two consecutive final full-suite runs from Phase A may satisfy PL-0269's global suite gate if PL-0269 implementation bytes are unchanged and both runs include the published PL-0269 code.

Create a **new** closure log:

`coordination/sessions/M12-C001/PL-0269_CODEX_LOG_V02.md`

The V02 log must:

- preserve the V01 blocker history;
- reference PL-0269 implementation SHA `c6f935fc0308256af528cc596ff01e55d3242763`;
- reference the shared cancellation-remediation SHA;
- record the 20x deterministic cancellation proof;
- record the two consecutive green locked full suites;
- record the re-run PL-0269 focused/static gates;
- make no audit acceptance claim;
- end exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Publish the V02 log in a separate log-only commit.

Update the builder master table so PL-0269 points to V02 closure evidence and is `READY_FOR_INDEPENDENT_AUDIT`.

# Phase C - Resume M12 continuously at PL-0270

If and only if Phase A and Phase B are fully green, resume the existing frozen child packages in exact order:

**PL-0270 through PL-0288**

Use each existing V01 child prompt and matching V01 audit criteria already present under:

`coordination/sessions/M12-C001/`

For every remaining child:

1. re-read its frozen prompt/criteria/pre-reads;
2. implement only that child;
3. run focused/predecessor/full/static/scope/security checks;
4. publish implementation/evidence commit(s);
5. publish separate child-log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`;
6. verify remote visibility;
7. update both the original M12 master log and this continuation log with exact SHAs/results;
8. continue immediately while green.

Do not wait for intermediate ChatGPT audit.

## Frozen authority rules

All original M12 rules remain in force:

- Scan Master remains immutable.
- Design Model/library/assembly/freeform/flexible-pack authorities stay separated.
- `METRIC_UNVERIFIED` / `mm_unverified` remains unverified.
- `DEFERRED_OWNER_VALIDATION` remains explicit.
- No physical/mold/manufacturing/certification claim.
- No private/raw scan evidence in reusable fixtures or presets.
- No silent/unlicensed library import or network auto-download.
- No M13 CAD/BREP/OpenCascade/STEP implementation.

## Stop conditions

Stop the whole batch on a real:

- failed validation not correctable within frozen scope;
- new locked-suite failure after remediation;
- synchronization/tracker mismatch;
- architecture/provenance/authority conflict;
- dependency/license/privacy/security issue;
- owner-required decision;
- need to start M13/later work.

On stop:

1. publish exact blocker evidence;
2. mark original master and continuation log `BATCH_STOPPED`;
3. record exact frontier/reason;
4. preserve all earlier green evidence;
5. end continuation log exactly `AWAITING_MILESTONE_AUDIT`;
6. stop.

## Successful handoff

After PL-0288 completes green:

1. original `MASTER_CODEX_LOG_V01.md` must accurately contain PL-0268 through PL-0288 status/SHAs/results;
2. continuation log must record remediation + PL-0269 V02 closure + all resumed children;
3. set batch status `BATCH_COMPLETED`;
4. verify local/origin/GitHub `main` parity and clean execution worktree;
5. confirm M13 was not started;
6. publish final master/continuation log-only evidence;
7. end the continuation log exactly:

`AWAITING_MILESTONE_AUDIT`

Stop for independent ChatGPT audit.
