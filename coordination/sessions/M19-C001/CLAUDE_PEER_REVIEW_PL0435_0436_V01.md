# Claude Peer Review: PL-0435 and PL-0436 (V01)

Date: 2026-11-10
Reviewer: Claude (independent peer reviewer; did not author the code)
Code under review: Codex code published in `260beb49`, with the ruff/mypy fixes in `0176a67e`. Reviewed at HEAD `f2fb75e6` (`main`, clean tree).
Mode: read-only review. No source, test, doc or `TASKS.md` edits. Mutants ran only on a temp copy. No model, checkpoint or weight was downloaded, opened or loaded.

## Verdicts

| Task | Verdict |
|---|---|
| PL-0435 AI Visual Reference lane | **PASS**: eligible for `CLAUDE_PEER_AUDITED_PASS` at prototype tier. Only P3 findings. External model/licence gates stay pending. |
| PL-0436 Commercial neural reconstruction backend | **CHANGES_REQUIRED**: three P2 findings (one security, one provenance, one spec gap) and P2 test gaps on the licence and worker trust boundary. |

## Evidence I ran

- Focused suites (`.venv`, `QT_QPA_PLATFORM=offscreen`): `test_visual_reference.py`, `test_visual_reference_viewport.py`, `test_neural_reconstruction_backend.py`, `test_neural_reconstruction_io.py`, `test_neural_reconstruction_runtime.py`, `test_vggt_checkpoint.py`, `test_vggt_worker_protocol.py`. Result: **96 passed, 8 skipped**.
  - 6 skips: `test_vggt_checkpoint.py` needs torch/safetensors, which this venv does not have. So the streaming loader is never exercised locally or in CI.
  - 2 skips: Windows symlink creation is unavailable.
- `ruff check core apps tools tests`: All checks passed.
- `mypy core apps tools`: Success, 288 files, no issues.
- Hosted CI (`gh run list --branch main --limit 6`):
  - Windows Python Quality runs the full `uv run --locked pytest -q`.
  - The last completed run, 42891181899 at `4009a263` (which includes `260beb49`), passed.
  - Run 42892397185 at `f2fb75e6` was still in progress at review time.
  - Signing Material Guard: green.
- Lazy-import check: importing `vggt_worker`, `neural_reconstruction*`, `vggt_checkpoint` and `visual_reference` loads none of torch, vggt, safetensors, huggingface_hub, transformers, PIL or numpy. Confirmed.
- Dependency and download scan:
  - No torch, vggt, safetensors or huggingface entry in `pyproject.toml` or any lock or requirements file.
  - No `from_pretrained`, `hf_hub_download`, `snapshot_download`, urllib, requests or http use in the reviewed modules.
  - `NEURAL_EXPERIMENTAL` is not registered or selected anywhere outside these modules, so COLMAP/OpenMVS stays the only wired and default backend.

### Mutation testing

18 hand mutants on a temp copy. Baseline was green.

| Mutant | Result |
|---|---|
| M3 sidecar `generated=False` | killed |
| M4 overlay suppressed | killed |
| M6 promotion helper no-ops | killed |
| M1 `remove_visual_reference` kind guard removed | **survived** |
| M2 negative seed accepted | **survived** |
| M5 `checkpoint_sha256` digest not validated | **survived** |
| N1 activation SHA pin dropped | killed |
| N5 child env keeps HF tokens | killed |
| N6 non-finite PLY rows accepted | killed |
| N7 timeout does not kill the worker | killed |
| N10 camera order check dropped | killed |
| N11 publish METRIC_VERIFIED check dropped | killed |
| N12 cleanup ignores the ownership marker | killed |
| N2 activation `checkpoint_id == facebook/VGGT-1B-Commercial` dropped | **survived** |
| N3 worker upstream code-commit pin dropped | **survived** |
| N4 worker output-path containment dropped | **survived** |
| N8 worker image digest check dropped | **survived** |
| N9 subprocess-engine SHA pin dropped | **survived** |

## PL-0435: AI Visual Reference lane

### Hard isolation (focus 1): holds

- `VisualReferenceRecord` (`core/src/packlab_core/visual_reference.py:112-153`) carries no geometry samples.
- `generated`, `authority_class=AI_VISUAL_REFERENCE` and the caveat are read-only properties, so they cannot be set to anything else.
- Promotion fails closed (`:184-189`).
- Downstream authority gates are allowlists that existed before this work, not deny-lists:
  - Scan Master requires `generated is False` and `authority_class == "OBJECT_CAPTURE_GEOMETRY"` (`scan_master.py:165`).
  - Scan Master export and profile require `SCAN_MASTER`.
  - The captured-geometry fit gate rejects `AI_VISUAL_REFERENCE` explicitly (`captured_geometry_fit_gate.py:433`) and requires `OBJECT_CAPTURE_GEOMETRY` (`:455`).
  - Scale provenance and registration record `ai_visual_reference_measurement_authority: False`.
- In Studio, only `viewport.py` consumes the record. No Studio measurement tool samples `SceneModel` geometry. `closure_workflow` takes only `CAP`.
- `SceneObject.__post_init__` (`viewport.py:400-403`) binds the AI kind to a record in both directions.
- `remove_visual_reference` (`:721-733`) refuses non-AI kinds.
- The PNG sidecar keeps `generated`, `authority`, `caveat` and `visibility`. Redaction does not strip these keys.

### Other focus areas

- Licensing: no backend, SDK or checkpoint exists. The lane is inert until an adapter is written.
- Feature flag and fallback: the lane has no backend implementation, so it is off by default.
- Determinism: settings are canonical JSON and the seed is recorded.

### Findings

- **P3** `apps/windows-studio/src/packlab_studio/viewport.py:413-419`: authority and caveat strings are hardcoded copies instead of `record.authority_class` / `record.caveat`. A drift risk only.
- **P3** `viewport.py:558-573`: AI geometry is drawn in the same colours as scan geometry. Only the global banner at `:529-538` marks it, so with several objects visible a user cannot tell which one is generated. The spec's persistent state is met, but per-object styling (tint or dashed outline) is recommended.
- **P3** `viewport.py:702-719`: `add_visual_reference` does not bind the supplied geometry to `record.artifact_sha256`, so any geometry can be shown under any record. Display-only, so low risk.
- **P3** `viewport.py:486-493`: `SceneModel.bounds()` includes AI geometry, so `fit_to_view` frames invented geometry. Display only, but worth excluding or flagging.
- **P3** Spec items not implemented, both acceptable at prototype tier:
  - OBB display placement (optional in the spec).
  - A Studio shell/UI toggle. Hiding works at the service level only (`set_visible`); no shell or menu wiring.
- **P3** Test gaps:
  - M1: no test that `remove_visual_reference("captured-scan")` raises.
  - M2: no negative/bool seed test.
  - M5: no invalid `checkpoint_sha256` test.
  - No explicit "model replacement does not affect authority code" test.
  - The viewport `SceneObject` path is not fed to the real Scan Master or fit gate. Isolation there relies on the structural allowlists above.
- **P3** Codex log claim, "Removal is restricted to the visual-reference kind": true in code, but untested (M1).

## PL-0436: Commercial neural reconstruction backend

### Licence gating (focus 2): sound in code

The non-commercial checkpoint is not loadable through the reviewed code paths:

- Activation requires all of the following (`core/src/packlab_core/neural_reconstruction.py:84-93`):
  - `checkpoint_id == "facebook/VGGT-1B-Commercial"`
  - HF revision `ebb29a53…`
  - checkpoint SHA `2b766b28…`
  - a strict-bool owner acceptance
  - four evidence references
- The subprocess engine rejects any size or SHA other than the commercial pin (`neural_reconstruction_runtime.py:111-125`).
- The worker rejects any other size, SHA or upstream commit (`vggt_worker.py:157-167`), re-hashes the file (`:202-209`), loads through the streaming loader with a before/after `lstat` identity check, and re-asserts the SHA after load (`:332`).
- No auto-download path:
  - `VGGT()` is constructed without `from_pretrained`.
  - `HF_HUB_OFFLINE` and `TRANSFORMERS_OFFLINE` are set and HF token env vars are removed in both parent and child.
  - Limit: this is env-flag-based, not a network sandbox. `torch.hub` is not covered by those flags (P3).
- Probing imports no model libraries.
- `NEURAL_EXPERIMENTAL` is never default.
- `METRIC_VERIFIED` is rejected at three layers.

### Findings

- **P2 (security, pin bypass)** `neural_reconstruction_runtime.py:230-245`: the worker is launched as `python -B -m packlab_core.vggt_worker` with `cwd=output_root`. With `-m`, Python puts the cwd at the front of `sys.path`, ahead of `PYTHONPATH` (core source, then the pinned upstream root). Reproduced in scratch: with a decoy `vggt/` package in the cwd, `import vggt` resolved to the cwd copy, not the `PYTHONPATH` upstream.
  - Effect: any `vggt/`, `torch/`, `numpy/` or `packlab_core/` entry in the runtime output root shadows the pinned code. That defeats the `git rev-parse` / `status --porcelain` verification of `upstream_root` (`vggt_worker.py:176-200`).
  - Related: the whole parent environment is inherited (`:65`), and `-s` / `-E` are not used.
  - Fix: launch with `-P` (Python ≥3.11, which stops the cwd from being prepended) plus `-s`, and/or use the private temp dir as cwd. Add a test that asserts the argv flags and cwd.
- **P2 (provenance)** `neural_reconstruction.py:281-297` vs `:424-433`: the persisted `derived/reconstruction/<rev>/manifest.json` is written with `backend_build="injected-runtime"` and `backend_license="configured-vggt-checkpoint"` (placeholders). The checkpoint ID/revision/SHA and licence ID are applied only to the in-memory object returned by `VGGTReconstructionBackend.execute`. So the durable artifact lacks the model provenance the spec requires, and it disagrees with the returned manifest.
  - Related (P3): if `execute` fails after publication, for example because activation became incomplete at `:421-423`, the published directory stays on disk while the run reports FAILED.
  - Fix: pass the activation identity into `VGGTWorkspaceRuntime` before publishing, and add a test that reads `manifest.json` back.
- **P2 (spec gap: confidence)** `vggt_worker.py:347-389`: the spec's "Normalized outputs must include … confidence" is not met. The worker drops VGGT's point/depth confidence and emits only XYZ, and there is no confidence artifact or field. Either emit a bounded confidence channel (for example a per-point property or summary statistics) or record an explicit deferral and limitation that a reviewer accepts.
- **P2 (test discrimination on trust and licence boundaries)**:
  - N2: dropping the `checkpoint_id == facebook/VGGT-1B-Commercial` check survives. The only negative test (`tests/core/test_neural_reconstruction_backend.py:237-249`) pairs `"facebook/VGGT-1B"` with `"bad-hash"`, so the non-commercial ID is never isolated. This is the headline requirement of the task.
  - N3, N4, N8: worker request validation of the upstream commit pin, output-path containment and image digest is untested. Only the unpinned checkpoint, duplicate-key and oversize cases are covered.
  - N9: the subprocess-engine SHA pin is untested; the existing test fails on size first.
  - There is no end-to-end `VGGTSubprocessWorkspaceEngine.infer` test with a stub worker.
- **P3** `vggt_worker.py:31-33` / `neural_reconstruction_runtime.py:40`: pins are duplicated as literals, so they can drift. Import them from one module, or add an equality test.
- **P3** `neural_reconstruction.py:91`: `checkpoint_license_id` is any token. A string like "CC-BY-NC-4.0" would pass. The SHA pin makes this non-exploitable, but an allowlisted licence ID (for example `VGGT-License`) would make the record self-consistent.
- **P3** `vggt_worker.py:180-200` / `runtime.py:159-172`:
  - `git -C <upstream_root>` honours that repository's config (for example `core.fsmonitor`). The upstream root is owner-configured, so this is low risk; consider `-c core.fsmonitor=false` and `safe.directory`.
  - `status --porcelain` ignores gitignored files such as a stale `__pycache__`.
- **P3** Process cleanup (`runtime.py:277-300`): cancel and timeout terminate or kill the direct child only, and there is no Windows job object. If the parent dies, the worker is orphaned for up to 3600 s.
- **P3** Determinism:
  - Revision IDs are `uuid4` (acceptable).
  - Torch seed and deterministic algorithms are not set.
  - Point sampling is deterministic (stride-based).
  - The preprocessing transform (pad/scale to 518) assumes the behaviour of `load_and_preprocess_images_square` at the pinned commit and PIL size without EXIF transpose. Unverified without real inference.

### Worker protocol checks that hold (focus 3)

- Request and result size caps: 1 MiB and 4 MiB.
- Duplicate-key rejection.
- Exact field sets.
- Image count capped at 1..100.
- Asset-ID traversal guards.
- Absolute regular non-reparse inputs.
- Outputs must be the fixed names inside the private request directory and must not already exist.
- Exclusive-create error file with no exception text.
- PLY validation: full header/count/finite rows, 12 MiB cap.
- Camera finite and order checks.
- Lifetime capped at 3600 s, with kill on timeout and terminate/kill on cancel.
- Temp directory cleanup.
- Owned-artifact cleanup limited to marked regular files under the root.

### Codex log claims vs reality (focus 6)

- V08's "80 passed, 8 skipped" for the five PL-0436 modules is consistent with my 96/8 across seven modules (83 for the PL-0436 subset now, after later additions).
- The claims of lazy imports, offline env, token stripping and bounds are verified.
- The claim that strict cleanup is limited to marked regular files is verified.
- Not verifiable here, and not claimed as executed:
  - The V02 local hash match of the downloaded checkpoint at `%LOCALAPPDATA%`.
  - The upstream clone at commit `a288dd0f…`.
- The log's "SOURCE_REVIEW_PASS / SECURITY_REVIEW_PASS" were Codex-era internal reviews. They are not `CLAUDE_PEER_AUDITED_PASS`. They did not catch the cwd shadowing or the provenance gap.

## Must remain externally pending

### PL-0435

- Selection of any real generator (SAM 3D Objects, TRELLIS or other).
- Separate code and checkpoint licence records, commercial-use and redistribution review, and a pinned checkpoint hash.
- Owner acceptance.
- No backend may be enabled before these.

### PL-0436

- Legal review of the VGGT License and AUP for PackLab's actual deployment. The Codex V02 notes list prohibited-use categories including critical infrastructure, transport and heavy machinery, which are potentially relevant to factory/mould use and need a legal determination.
- Distribution and redistribution, with AUP and licence presentation to end users.
- Runtime dependency licence review: torch, numpy, Pillow, safetensors, and the upstream vggt code at `a288dd0f`.
- Owner-side independent re-verification of checkpoint SHA `2b766b28…` against the HF LFS pointer for revision `ebb29a53…`.
- Real CPU/GPU inference. This was never run; the RAM gate was below the checkpoint size.
- The PL-0437 controlled COLMAP/OpenMVS vs neural benchmark with physical ground truth, before any default change.

## Required to clear PL-0436 (narrow)

1. Launch the worker so the cwd and user-site are not importable (`-P -s` or equivalent), and add a test.
2. Persist the activation identity and licence into the published `manifest.json`, and add a read-back test.
3. Emit confidence, or record an accepted explicit deferral and limitation.
4. Add isolated tests that kill mutants N2, N3, N4, N8 and N9.

After those fixes a narrow re-review is enough.
