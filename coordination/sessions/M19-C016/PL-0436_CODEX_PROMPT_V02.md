# PL-0436 Codex Prompt V02 — VGGT Neural Backend Adapter Contract

Date: 2026-10-23  
Owner authorization: delegated PackLab implementation and queue sequencing. VGGT is the model family named by the PL-0436 implementation spec and remains this task's integration target. This does not mean the owner accepted VGGT terms, requested gated access, or authorized checkpoint download/activation. Hugging Face is currently the official gated distribution point for the commercial checkpoint, not a required PackLab runtime service. This prompt supersedes the V01 preflight-only implementation boundary while retaining all mandatory licensing safeguards.

## Mandatory pre-read

Read `docs/implementation/PL-0436_COMMERCIAL_NEURAL_RECONSTRUCTION_RESEARCH.md` in full. Treat its pre-install licensing gates, PL-0163 contract and authority boundary as binding.

## Objective

Implement the PackLab-side VGGT integration adapter contract behind the existing PL-0163 `ReconstructionBackend` protocol. Keep VGGT imports/runtime construction behind an injected boundary and exercise the adapter only with a synthetic runtime. Leave real model/runtime loading unavailable until the exact VGGT checkpoint has verified license, identity, runtime and deployment records.

## Allowed scope

- Add a VGGT-targeted adapter and small immutable config/result types in `core/src/packlab_core/`; do not couple downstream PackLab code to VGGT classes.
- Add focused synthetic tests under `tests/core/` using an in-memory fake runtime and fake license records only.
- Add a neural experimental backend ID to the common reconstruction contract only where required for protocol conformity.
- Update this session's criteria/log, root `TASKS.md`, and `project-control/codex/jobs/PL-0436/job.json`.
- Do not substitute another model or make the application depend on Hugging Face. Do not access any model host.

## Hard constraints

- Do not sign into or request access from Hugging Face or any other model provider; do not accept terms; do not download, install, load or execute any checkpoint or neural runtime.
- Without complete explicit license/checkpoint/runtime/deployment gate data plus an injected runtime, `probe()` must report unavailable and `execute()` must fail closed with a clear reason.
- Never emit `METRIC_VERIFIED`; retain only `RELATIVE` or `METRIC_UNVERIFIED`. Preserve source input digest and immutable input identity. Keep local model paths and credentials out of all portable provenance.
- Fake acceptance/config values in tests are synthetic contract fixtures and must never be described as actual owner approval.
- Zero Actions/paid CI, no PR, no source push to `main`, no native OCCT/OCP, no Installer, preserve Desktop PackLab and OwnerDev.

## Validation and handoff

Run focused synthetic core tests with the existing `.venv`, targeted Ruff and `git diff --check`. Record exact outcomes, initial failures/fixes, synthetic-only scope, VGGT as the specified target, and the remaining checkpoint/license/runtime/deployment gates. Do not mark PL-0436 fully complete until the specified VGGT checkpoint and the frozen pre-read's licensing and identity criteria are evidenced.
