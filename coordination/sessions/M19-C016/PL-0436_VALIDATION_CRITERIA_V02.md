# PL-0436 Validation Criteria V02 — VGGT Neural Backend Adapter Contract

## Owner authorization addendum — 2026-10-23

The owner later explicitly confirmed VGGT/Hugging Face access approval, directed local download, completed authenticated access, and instructed Codex to finish the VGGT work. This supersedes V02's earlier prohibition on model-host access and local checkpoint download for this pinned checkpoint only. The owner-authorized local checkpoint download and SHA-256 verification are complete. Owner access/local-use approval is **not pending**. Criterion 7's activation/deployment references below mean technical readiness and future end-user packaging notices; they do not ask the owner to re-approve VGGT access or local use. No checkpoint weights have been loaded or executed. User-facing deployment preference recorded from the owner: PackLab is non-commercial, users should be able to use it, and its source code should not be exposed or downloadable.

1. VGGT-targeted adapter satisfies the common `ReconstructionBackend` protocol and rejects jobs for another backend ID, without downstream VGGT class coupling.
2. Missing runtime/configuration, missing pinned VGGT checkpoint identity/hash, incomplete terms acceptance, acceptable-use review, runtime license review or deployment review makes capability unavailable and execution fail closed with a clear diagnostic.
3. Synthetic fake runtime verifies normalized result/provenance, cancellation and source immutability without reading/writing source artifacts or loading a model.
4. Output accepts only relative or metric-unverified scale; `METRIC_VERIFIED` is rejected. Portable provenance includes model/checkpoint identity and digest only after explicit config, never a local path or secret.
5. Fake configuration/acceptance records exist only in tests and are labelled synthetic; they are not owner approval evidence.
6. Focused tests, targeted Ruff and `git diff --check` pass locally.
7. No alternate model substitution, Hugging Face runtime dependency, checkpoint/runtime installation or execution, Actions/paid CI, PR, source push to `main`, native/Installer build, or release claim. The owner-authorized download of the pinned checkpoint is complete; no checkpoint weights have been loaded or executed. VGGT remains the specified task target. Remaining work is technical inference readiness and, before user distribution, resolved-runtime notices plus the end-user VGGT AUP/license notice path. Do not request repeat owner access/local-use approval.
