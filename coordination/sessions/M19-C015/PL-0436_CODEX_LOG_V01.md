# PL-0436 Codex Log V01 — Neural Backend License/Checkpoint Preflight

Date: 2026-10-22  
Actor: Codex  
State: `BLOCKED_OWNER_ACCESS_AND_TERMS_ACCEPTANCE / NO_MODEL_DOWNLOAD / NO_BACKEND_ACTIVATION`

## Repository and synchronization

- Repository: `C:\Users\sekip\Desktop\PackLab` (`Sekiph82/PackLab`), branch `main`.
- Starting/final local commit: `f8745047063aca6c17378ecb33604e6e1e5b5f02`; `git fetch origin main` succeeded earlier in this run and local `HEAD` matched before local-only changes.
- Read the full mandatory pre-read `docs/implementation/PL-0436_COMMERCIAL_NEURAL_RECONSTRUCTION_RESEARCH.md`, PL-0436 prompt/criteria and current Project Status. The pre-read forbids the original non-commercial VGGT checkpoint and requires owner/license acceptance, pinned checkpoint identity/hash, deployment/redistribution review, acceptable-use restrictions and runtime dependency license review before installation.
- Existing owner/task changes were preserved. No reset, stash, rebase, commit or push occurred.

## Official-source evidence (checked 2026-10-22)

- Official project README: <https://github.com/facebookresearch/vggt/blob/main/README.md>. It distinguishes the original `VGGT-1B` checkpoint (not licensed for commercial usage) from `VGGT-1B-Commercial`, and says commercial use is restricted for military applications. It describes access to the commercial checkpoint as gated by an application workflow.
- Official VGGT license: <https://github.com/facebookresearch/vggt/blob/main/LICENSE.txt>. It defines the research materials to include model code and weights; use/distribution is bound by that agreement and redistribution requires providing recipients a copy. Its Acceptable Use Policy contains prohibited-use restrictions, including military/warfare and certain high-risk applications. It also disclaims warranties and assigns appropriateness and redistribution risk to the licensee. This log is a factual summary, not legal advice or counsel review.
- Official checkpoint page: <https://huggingface.co/facebook/VGGT-1B-Commercial>. It identifies the checkpoint license as `vggt-aup-license`, describes commercial use subject to a military-use exception, and requires users to agree to share their Hugging Face information before access.
- Official checkpoint file listing: <https://huggingface.co/facebook/VGGT-1B-Commercial/tree/main>. It reports two checkpoint files, `model.safetensors` and `vggt_1B_commercial.pt`, each shown as 5.03 GB. The page says files can be listed but not accessed without gated access. No file bytes or exact SHA-256 was available from the public listing.

## Result and remaining gates

- No owner Hugging Face account was accessed, no account data shared, and no click-through agreement was accepted.
- No checkpoint/runtime package was downloaded, installed or executed; no neural backend was implemented or activated. The original `facebook/VGGT-1B` checkpoint remains prohibited under the pre-read.
- Owner must personally review the gated checkpoint conditions, decide whether to share account information and accept them, and document the decision here in the project workflow. If accepted, the exact commercial checkpoint SHA-256 must be obtained and pinned before installation. Runtime dependency licenses and the intended bundled/redistributed versus local-only deployment model must then be reviewed against the license's redistribution-copy and use restrictions.
- The owner's stated intent that PackLab itself is non-commercial and that users should not receive source code is recorded as product intent; it does not waive third-party model access, checkpoint redistribution, acceptable-use or runtime licensing conditions.
- PL-0436 stays blocked. PL-0437 remains dependent on an approved backend and physical ground truth.
- No model/backend tests apply to this read-only preflight. The scoped queue metadata/tracker validator ran locally: `$env:PYTHONDONTWRITEBYTECODE='1'; .\\.venv\\Scripts\\python.exe -B -m pytest tests/ci/test_codex_task_queue.py -q` — **8 passed** (`0.06s`). This verifies local queue consistency only. Zero Actions/paid CI, no PR, no source push to `main`, no native/Installer build, no release claim.
