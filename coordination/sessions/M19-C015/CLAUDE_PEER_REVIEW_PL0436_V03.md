# CLAUDE PEER REVIEW: PL-0436 V03 (narrow re-review)

- Reviewer: independent Claude Code reviewer. I did not write the fix.
- Date: 2026-11-10
- Scope: commit `202d7e4d` ("require an activation record for the VGGT workspace runtime"). This review checks the single residual P2 from `CLAUDE_PEER_REVIEW_PL0434_0436_V02.md` (case B) and the F5 test gap.
- HEAD when reviewed: `8185773a`, working tree clean. I made no source, test, doc or tracker edits. All mutations ran on a temp copy.

## Verdict

| Task | Verdict |
|---|---|
| PL-0436 Commercial neural reconstruction backend | **PASS**: `CLAUDE_PEER_AUDITED_PASS`-eligible at prototype tier. The V02 P2 is closed. External gates stay open: VGGT licence/AUP legal review, real inference, and the PL-0437 benchmark. |

## The diff

- `neural_reconstruction.py:167`: `activation` is now a required keyword with no default.
- `neural_reconstruction.py:171`: the guard is now unconditional, so it rejects `None`, a non-record, or an incomplete record with `ValueError`.
- Tests:
  - Every existing workspace-runtime construction now passes `activation=_activation()`.
  - New `test_workspace_runtime_requires_an_activation_record` covers the missing keyword (`TypeError`) and `activation=None` (`ValueError`).
  - New `test_backend_rejects_a_runtime_published_under_a_different_licence` covers mutant F5.

## Commands and results

| Command | Result |
|---|---|
| `pytest tests/core/test_neural_reconstruction_backend.py tests/core/test_neural_reconstruction_runtime.py tests/core/test_vggt_worker_protocol.py tests/core/test_neural_reconstruction_io.py -q` | 95 passed, 2 skipped |
| `ruff check core tests` | All checks passed |
| `mypy core apps tools` | Success, 288 source files |
| `git grep VGGTWorkspaceRuntime` | Only callers: `neural_reconstruction.py` and `tests/core/test_neural_reconstruction_backend.py`. Every test call passes `activation=`. No app, tool or orchestrator constructs the runtime, so nothing else can break. |
| `gh run list --branch main --limit 4` | Windows Python Quality on `8185773a` (which contains `202d7e4d`) was still **in_progress** when I wrote this. Signing Material Guard: success. The previous Quality run on `856c7759`: success. |

## Probe: can the saved and returned identities differ?

I used the repo's own fixtures (`_workspace`, `SyntheticWorkspaceEngine`, `_job`, `_activation`) on temp directories. The probe script is in the session scratchpad and is not committed.

### Construction

| Case | Result |
|---|---|
| C1: `activation` keyword missing | `TypeError` |
| C2: `activation=None` | `ValueError` (incomplete) |
| C3: `owner_terms_accepted=False` | `ValueError` |
| C4: wrong checkpoint SHA | `ValueError` |
| C5: a dict instead of a record | `ValueError` |
| C6: empty licence ID | `ValueError` |

### Runs

| Case | Status | Returned identity | Saved `manifest.json` |
|---|---|---|---|
| R1: same activation in runtime and backend | SUCCEEDED | real SHA, `synthetic-vggt-license` | identical |
| R2: runtime licence differs from backend | FAILED | none | `other-licence-id` (directory left behind) |
| R3: cancelled after publish | CANCELLED | none | real identity (directory left behind) |
| R4: exception after publish | FAILED | none | real identity (directory left behind) |
| R5: backend activation incomplete | FAILED before runtime | none | nothing published |
| R6: non-`VGGTWorkspaceRuntime` wrapper delegating to a workspace runtime with a different licence | **SUCCEEDED** | `synthetic-vggt-license` | **`other-licence-id`** |

Case B from V02 can no longer be constructed. While `VGGTWorkspaceRuntime` is used directly, every outcome either returns the same identity that was saved or returns no manifest.

`complete` pins the checkpoint ID, revision and SHA to constants, so two complete records can differ only in `checkpoint_license_id`. The backend check compares that field, and R2 shows it fails closed.

R6 is the one remaining way the identities can diverge, and only through a runtime type the code does not provide (see P3-1).

## Mutation testing (temp copy, `PYTHONPATH` checked to resolve to the copy)

The backend test file passes 19/19 on the unmutated baseline.

| Mutant | Result | Killed by |
|---|---|---|
| M1: restore the pre-fix optional `= None` and conditional guard | KILLED | `test_workspace_runtime_requires_an_activation_record` |
| M2: drop `not activation.complete` | KILLED | `test_workspace_runtime_rejects_an_incomplete_activation` |
| M3: drop `isinstance` (`None` raises `AttributeError`) | KILLED | requires_an_activation_record |
| M4: restore the `= None` default but keep the guard | KILLED | requires_an_activation_record |
| M5: delete the guard | KILLED | both tests above |
| F5: delete the backend mismatch check | KILLED | `test_backend_rejects_a_runtime_published_under_a_different_licence` |
| F5b: weaken the check to compare the build only | KILLED | same test |

## Findings

**P0 / P1 / P2:** none.

**P3 (non-blocking):**

1. **The identity check depends on the runtime's type.**
   - Where: `neural_reconstruction.py:453`.
   - The saved-versus-returned check runs only when `isinstance(self._runtime, VGGTWorkspaceRuntime)`.
   - A delegating or wrapping `VGGTInferenceRuntime` that publishes through a workspace runtime under a different licence ID gets SUCCEEDED, and its returned identity is overwritten while the saved file keeps the other licence (probe R6).
   - This is latent: there is no wrapper and no production caller. A stronger fix would read back the published `manifest.json`, or let the runtime report the identity it saved.
2. **Stale code and comments.**
   - `:173-174` still says "When supplied".
   - The `activation` property is still typed `VGGTActivationRecord | None` (`:182`).
   - `_published_identity` still accepts `None`, and the backend's `self._runtime.activation is not None` (`:454`) can no longer be false.
   - These are harmless cleanups. The `None` branch of `_published_identity` is unreachable from the workspace runtime.
3. **Orphan directories (carried over from V01/V02).** Runs that fail or are cancelled after publishing leave the published directory on disk (R2, R3, R4). Its identity is internally consistent, but no run record references it.
4. Every other V02 P3 item is unchanged. These include F3 `cwd`, F7 junction tests, decoy `-c` vs `-m`, the environment allowlist, the `-P` Python version, confidence disclosure, and the earlier carried items.

## Conditions and external gates (PL-0436 stays prototype tier)

- Hosted Windows Python Quality on `8185773a` was still running. Confirm it is green before marking the task `[x]`.
- These must remain externally pending:
  - VGGT licence/AUP legal review, plus redistribution, deployment and runtime-dependency licence review.
  - Owner re-verification of the checkpoint SHA.
  - First real CPU/GPU inference, with confidence output.
  - The PL-0437 benchmark before any default change.
- `NEURAL_EXPERIMENTAL` stays non-default. Its output stays `RECONSTRUCTION_OBSERVATION`, and `METRIC_VERIFIED` is rejected.
