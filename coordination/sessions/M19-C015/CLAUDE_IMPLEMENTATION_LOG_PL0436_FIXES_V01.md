# Claude implementation log — PL-0436 review fixes (V01)

Date: 2026-11-10. Implementer: Claude Code. This is not a review. It responds to
`coordination/sessions/M19-C001/CLAUDE_PEER_REVIEW_PL0435_0436_V01.md`.

| Finding | Change |
| --- | --- |
| P2 security: worker import shadowing | The worker now runs with `python -B -P -s -m packlab_core.vggt_worker` from its **private per-job temp directory** (previously the shared output root). `-P` stops `-m` from putting the working directory first on `sys.path`; `-s` skips user site-packages. The command is built by `_vggt_worker_command`. A test plants a decoy module in the working directory: the protected command cannot import it, and a control run without `-P` does. |
| P2 provenance: saved manifest | `VGGTWorkspaceRuntime(..., activation=)` writes the real `checkpoint_id@revision#sha256:…` build and the licence ID into the published `manifest.json`; an incomplete activation is refused. The backend rejects a workspace-runtime manifest whose identity differs from its activation. A read-back test checks that the saved file contains the SHA and licence and no placeholders. |
| P2 test gaps N2, N3, N4, N8, N9 | Isolated tests for: the non-commercial checkpoint ID with the correct SHA (N2); a different well-formed upstream commit (N3); an output path outside the private directory (N4); image bytes that differ from the digest at the same size (N8); the engine refusing the right size with the wrong SHA (N9). The worker-side tests patch the pins to a tiny synthetic checkpoint and stub git. |
| **New bug found by these tests** | `read_worker_request` rejected **every** valid request with "worker output path already exists": `_is_reparse()` returns True for paths that do not exist yet, and the output paths are always new. Real inference had never run, so this was never exercised. The check is now `os.path.lexists(output_path)`, which still refuses existing files, broken links and junctions. Covered by a happy-path test and an existing-output test. |
| P2 spec gap: confidence | **Explicit deferral (not implemented).** The worker writes XYZ points only and drops VGGT's per-point confidence. Emitting confidence needs the real model forward pass, which cannot be exercised here (no torch, RAM below checkpoint size). Until it is implemented, VGGT output carries no confidence and must not feed confidence-gated decisions. The output keeps `authority_class=RECONSTRUCTION_OBSERVATION` and stays experimental (`NEURAL_EXPERIMENTAL`, not wired as default). This must be implemented and tested together with the first real-inference run (PL-0437 benchmark gate). |

Not addressed (P3):
- duplicated pin literals across modules;
- licence-ID allowlist;
- `torch.hub` offline flag;
- Windows job object for the process tree;
- torch seeding;
- a folder left published after a later failure.

Still external: legal review of the VGGT licence and acceptable-use policy (including prohibited uses that may matter for factory and mould contexts); a redistribution review; dependency licences; the owner re-verifying the checkpoint SHA; real inference; the PL-0437 benchmark.
