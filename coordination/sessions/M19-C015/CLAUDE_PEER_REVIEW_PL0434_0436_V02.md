# Claude Peer Review: PL-0434 (narrow) and PL-0436 (re-review), V02

Date: 2026-11-10
Reviewer: Claude (independent peer reviewer; did not write the fixes)
Code under review:
- `69a8c809`: PL-0434 test fix.
- `25fe5b65`: PL-0436 fixes.

Reviewed at HEAD `856c7759` (`main`, clean tree).

Mode: read-only. I made no source, test, doc or `TASKS.md` edits. Mutants ran only on a `git archive HEAD` copy in the session scratchpad. No model, checkpoint or weight was downloaded or loaded.

## Verdicts

| Task | Verdict |
|---|---|
| PL-0434 Packaging dossier PDF | **PASS**: `CLAUDE_PEER_AUDITED_PASS`-eligible at prototype tier. P2-6 is closed. P3-d (no check that the disclaimer is actually visible) remains, non-blocking. |
| PL-0436 Commercial neural reconstruction backend | **CHANGES_REQUIRED (narrow)**: one residual P2. A `VGGTWorkspaceRuntime` built without `activation=` still publishes a placeholder `manifest.json`, and the run still reports SUCCEEDED. The fix is one line plus one test. Every other V01 item is closed. External gates stay pending: licence/AUP legal review, real inference, and the PL-0437 benchmark. |

## Evidence I ran

### Focused tests

Run with `.venv` and `QT_QPA_PLATFORM=offscreen`. Result: **98 passed, 8 skipped**. Files:
- `test_neural_reconstruction_backend.py`
- `test_neural_reconstruction_io.py`
- `test_neural_reconstruction_runtime.py`
- `test_vggt_checkpoint.py`
- `test_vggt_worker_protocol.py`
- `test_packaging_dossier_pdf.py`

The skips:
- 6 because torch/safetensors are not installed.
- 2 because Windows symlink creation needs a privilege this account does not have.

### Lint, types and CI

- `ruff check core apps tools tests`: all checks passed.
- `mypy core apps tools`: success, no issues in 288 files.
- Hosted CI (`gh run list --branch main --limit 6`): run 42894481583 (Windows Python Quality, full locked pytest) at `856c7759`, which contains both commits, completed **success**. Signing Material Guard is green. The two earlier Quality runs were cancelled because later pushes superseded them.

### Mutation tests

19 hand mutants on the temp copy. Both baselines were green (neural 93 passed / 8 skipped; dossier 5 passed).

| Mutant | Result |
|---|---|
| d07 every provenance painted `UNKNOWN` | killed |
| d07b every provenance painted `SUPPLIER_FACT` (authority upgrade) | **killed** |
| d07c only `UNKNOWN` upgraded to `USER_DECLARED` | killed |
| d08 disclaimer reduced to `"PACKAGING METADATA ONLY. "` | **killed** |
| d08b one non-claim ("regulatory compliance") dropped | killed |
| N2 activation `checkpoint_id == …-Commercial` check dropped | **killed** |
| N3 worker upstream-commit pin dropped | **killed** |
| N4 worker output-path containment dropped | **killed** |
| N8 worker image digest check dropped | **killed** |
| N9 subprocess-engine SHA pin dropped | **killed** |
| F1 `-P` dropped from the worker command | killed |
| F2 `-s` dropped | killed |
| F3 `cwd=work` reverted to `cwd=output_root` | survived (P3, see below) |
| F4 runtime publishes placeholder identity | killed |
| F5 backend mismatch check removed | survived (P3) |
| F6 `lexists` reverted to `exists() or _is_reparse()` (the found bug) | killed |
| F7 `lexists` weakened to `exists()` | survived (P3; probe below shows the weakening is a real regression) |
| F8 output-exists check removed | killed |
| F9 runtime activation completeness check removed | killed |

## Scope A: PL-0434 narrow re-review

`tests/core/test_packaging_dossier_pdf.py:169-200` now asserts literal painted strings rather than values computed by the module's own helpers:
- six field/provenance pairs;
- the exact count of `"UNKNOWN  [UNKNOWN]"` (7);
- all four disclaimer non-claims.

Mutants d07b and d08 were the reason for P2-6, and both are now killed. So are the stricter d07c and d08b variants. The test records `QPainter.drawText`, so it still cannot prove that the text is visible: P3-d (white pen, zero rectangle) remains open, as the V02 review already allowed. The PL-0428 part of `69a8c809` is outside this review's scope.

**PL-0434: PASS.**

## Scope B: PL-0436 re-review

### 1. Worker import shadowing (V01 P2): closed

The worker now runs as `python -B -P -s -m packlab_core.vggt_worker` with `cwd` set to the private per-job directory (`neural_reconstruction_runtime.py:76-92, 249-252`). I ran the real `_vggt_worker_command` / `_vggt_worker_environment` in scratch.

**Cwd decoys.** I planted these in the cwd:
- `packlab_core/{__init__,vggt_worker}.py`, `vggt/__init__.py`;
- `sitecustomize.py`, `usercustomize.py`;
- a stdlib-shadowing `argparse.py`;
- a `.pth` file.

**Environment decoys.** The inherited `PYTHONPATH` pointed at the cwd, and `PYTHONSTARTUP` pointed at a decoy.

Results:
- **New launch:** none of the decoys ran. `vggt` resolved to the `PYTHONPATH` upstream copy and `argparse` to the stdlib. `sys.path[:2]` was `[core/src, upstream]`. The inherited `PYTHONPATH` is overwritten (`:66`), and `PYTHONSTARTUP` is ignored because the run is non-interactive.
- **Control with the old launch (`-B -m`, no `-P`):** the decoy `packlab_core` package and the decoy `__main__` both ran. The V01 issue is reproduced and is now blocked.
- **User site** (redirected with `PYTHONUSERBASE`; the real user site was not touched): planted `usercustomize.py` and `.pth` files did not run under `-s`. This venv already disables the user site, so `-s` matters for a non-venv worker interpreter.

Residual risk is low and limited to a same-user attacker:
- The full parent environment is still inherited (`:65`, no `-E`). For example, `PYTHONPYCACHEPREFIX` was honoured in my probe, and `PYTHONHOME` / `PYTHONWARNINGS` would be too. Anyone who controls the parent's environment already controls the parent.
- `-B` stops `.pyc` files being written but not being read. A planted `__pycache__` under `core/src` or the upstream root would still load, and `git status --porcelain` does not report ignored files (V01 P3).
- `.pth` files in the interpreter's own site-packages still run. That is the trusted install location.

### 2. Saved manifest identity (V01 P2): fixed only on the opt-in path; residual P2

I probed with the repo's own fixtures:

| Case | Run status | Returned manifest | Saved manifest | Published dirs |
|---|---|---|---|---|
| A: runtime and backend have the same activation | SUCCEEDED | real identity | real identity | 1 (they agree) |
| B: runtime built **without** `activation=` | **SUCCEEDED** | real identity | **`injected-runtime` / `configured-vggt-checkpoint`** | 1 |
| C: runtime licence ID differs | FAILED (ValueError) | none | the mismatched identity | 1, left behind |

The test `test_published_manifest_file_carries_the_activation_identity` covers case A.

Separately, the saved file's `limitations` list is a superset of the returned one (two extra disclaimers). That is benign.

### 3. `_is_reparse` → `os.path.lexists` (found bug): confirmed correct

**The bug was real.** The worker's `_is_reparse` (`vggt_worker.py:93-100`) returns True when `lstat` fails, so every new output path was refused. Mutant F6 restores the old code, and the new happy-path test `test_pinned_synthetic_request_is_accepted` kills it.

**The fix still refuses existing entries.** I probed `read_worker_request` with synthetic pins:

| Entry at the output path | Result |
|---|---|
| none (fresh path) | accepted |
| existing file | refused |
| existing directory | refused |
| `mklink /J` junction to an existing directory | refused |
| broken junction (`exists=False`, `lexists=True`) | **refused** |
| broken file symlink | could not test (`WinError 1314`, no symlink privilege) |

`lexists` uses `lstat`, so a broken file symlink would also be refused. Under the F7 weakening (`exists()` only), the broken junction is **accepted**, so the `lexists` choice matters. The worker also writes its outputs with exclusive-create (`open("x")` / `open("xb")` at `:281`, `:424`), which guards the window between this check and the write.

**No other caller breaks valid runs.**
- In the worker, `_is_reparse` is used only on paths that must already exist: the request file, checkpoint and images through `_regular_file`, and `source_root` at `:177`.
- In the parent, `_is_reparse_path` (`runtime.py:316`) is used only on existing prerequisites (`:162-174`) and on post-run outputs (`:360`, `:443`).

### 4. Confidence deferral: acceptable at prototype tier

- The reconstruction contract has no confidence field at all, so no current consumer can gate on missing confidence.
- `NEURAL_EXPERIMENTAL` is still not registered or selected outside these modules, and COLMAP/OpenMVS stays the default.
- Output keeps `authority_class=RECONSTRUCTION_OBSERVATION`, and `METRIC_VERIFIED` is rejected.
- The doc's Authority section bars default use before PL-0437.
- The deferral is recorded in the implementation log and in `TASKS.md`.

I accept it, provided it stays an open PL-0436/PL-0437 item tied to the first real-inference run. P3: the durable `manifest.json` does not itself say that confidence is absent.

### 5. Test gaps N2/N3/N4/N8/N9: closed

All five are killed by new isolated tests. N3 is killed by the pin check's own error message; real git would also refuse the commit.

### Findings

**P2 (blocking, narrow), provenance.**
- Location: `core/src/packlab_core/neural_reconstruction.py:167` (`activation` defaults to `None`) and `:453-458` (the check is skipped when `self._runtime.activation is None`).
- The problem: a `VGGTWorkspaceRuntime` constructed without an activation still writes the V01 placeholder identity to the durable `manifest.json`. The backend then returns SUCCEEDED with the real identity. That is the same saved-versus-returned divergence V01 blocked on, still reachable through the default argument with no error (probe case B). The comment at `:450-452` ("so the saved and returned manifests agree") is not true in that case.
- Fix: fail closed in the backend when the runtime is a `VGGTWorkspaceRuntime` whose `activation` is `None`. That means dropping `self._runtime.activation is not None and` so that `None` is treated as a mismatch, or making `activation` required. Then add a test for case B.
- No production code constructs these classes yet, so this is latent. It is still a traceability gap the fix claims to close.

**P3 (non-blocking).**
- **Mismatch check untested.** `neural_reconstruction.py:453-458` has no test (mutant F5 survives). Case C shows the check works. Also, as in V01, the rejected run leaves its published directory on disk.
- **Junction cases untested.** `vggt_worker.py:259` has no junction or broken-junction test (mutant F7 survives). `mklink /J` needs no privilege on Windows, so such a test is feasible.
- **`cwd` not pinned by a test.** `neural_reconstruction_runtime.py:252` (`cwd=work`) is not asserted (mutant F3 survives). With `-P` this is defence in depth only.
- **Decoy test uses `-c`, not `-m`.** `tests/core/test_neural_reconstruction_runtime.py:~300-303` runs the decoy check as `-c`, while the real worker runs as `-m`. My probe covered the real `-m` command.
- **Environment inherited wholesale.** `neural_reconstruction_runtime.py:65`: consider an allowlisted child environment (for example `SYSTEMROOT`, `PATH`, `TEMP`/`TMP`, plus the variables set here).
- **`-P` needs Python ≥3.11.** A separately configured older worker interpreter fails closed with exit 2 and only the generic "worker failed" message. `available()` does not check the version.
- **Confidence absence not disclosed.** Neither `_WORKER_LIMITATIONS` (`neural_reconstruction_runtime.py:42-46`) nor the worker's own list (`vggt_worker.py:386-390`) says that no confidence is emitted.
- Carried over from V01: duplicated pin literals, licence-ID allowlist, `torch.hub` offline, Windows job object, torch seeding, gitignored `__pycache__`.

## Must remain externally pending (PL-0436)

- Legal review of the VGGT licence and AUP, including prohibited-use categories relevant to factory/mould use.
- Redistribution and deployment review.
- Runtime dependency licences.
- Owner re-verification of checkpoint SHA `2b766b28…`.
- First real CPU/GPU inference, together with confidence output.
- PL-0437 benchmark before any default change.

## To clear PL-0436

Make case B fail closed and add its test. A narrow re-review of that diff is sufficient. The P3 items are recommended but not required.
