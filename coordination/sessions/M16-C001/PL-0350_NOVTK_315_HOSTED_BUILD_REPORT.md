# PL-0350 Hosted Build — Evidence and Blocker Report

Date: 2026-10-12
Status: **BATCH_STOPPED_AT_PL-0350 / AWAITING_INDEPENDENT_AUDIT**
Blocker: `CAPACITY_PREFLIGHT_SETUP_PYTHON_VERSION_UNAVAILABLE`

## Outcome

The implementation is published to GitHub `main` at `ca167dda2fe5c11de3f45e0285fe80b573194c48`, and exact-SHA Windows Python Quality passed. One authorized cold workflow dispatch was attempted. It failed in the first capacity-preflight setup step because `actions/setup-python` could not find CPython `3.12.15` x64 on `windows-2022`. Disk/storage measurement and the official source dry-run were therefore skipped in GitHub Actions; all native jobs were skipped. In accordance with the frozen prompt, no retry and no warm-cache run were dispatched.

**This does not meet PL-0350 acceptance.** No hosted OCCT SDK, OCP binary, packaged runtime smoke, redistribution clearance, installer, or cache-hit evidence exists from the dispatched run.

## Revisions and run evidence

| Evidence | Revision / result |
| --- | --- |
| Canonical start | `43a3f9fbed20fac614b3775c5b8929a9b828d4c3` |
| Safety-only workflow gate | `ef2b43bedcec9862653895c630fa23730a83f2d2` |
| Product implementation | `ca167dda2fe5c11de3f45e0285fe80b573194c48` |
| GitHub Python Quality | [38240270762](https://github.com/Sekiph82/PackLab/actions/runs/38240270762), success, 3m23s |
| Authorized cold dispatch | [38240655846](https://github.com/Sekiph82/PackLab/actions/runs/38240655846), failure, exact implementation SHA |
| Failed preflight job | [114782149441](https://github.com/Sekiph82/PackLab/actions/runs/38240655846/job/114782149441), setup-python failed |
| OCCT job | [114782264885](https://github.com/Sekiph82/PackLab/actions/runs/38240655846/job/114782264885), skipped |
| OCP job | [114782265710](https://github.com/Sekiph82/PackLab/actions/runs/38240655846/job/114782265710), skipped |
| Studio package job | [114782265731](https://github.com/Sekiph82/PackLab/actions/runs/38240655846/job/114782265731), skipped |

The exact failed step output was: `The version '3.12.15' with architecture 'x64' was not found for Windows 2022.` No preflight measurements, build artifacts, cache keys, or native output were generated. The Actions artifact download command confirmed `no valid artifacts found to download` for this run.

## Source patch and validation evidence

The separately verified public OCP source asset was `OCP_src_stubs_Windows.zip`, release 7.9.3.1.1, source revision `d69b064a3a604ebf245b1f3b14fb54c835a3a571`, 6,481,047 bytes, SHA-256 `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`. The bounded real-archive patch preflight verified 319 input modules / 638 registration entries and an output of 315 modules / 630 retained registrations after removing exactly `IVtk`, `IVtkOCC`, `IVtkTools`, and `IVtkVTK`. This was local source preparation evidence, not a native build. Patched `OCP.cpp` SHA-256 was `28c88f6fa3c8e366a26add8fb145f7177f1e376c1b068857b247ab2fac349faf`; patched CMake SHA-256 was `50ad079ba6686afc220b7b278ffd13a8e65dadb69a4bcf548eb50752c922ed19`; patch manifest SHA-256 was `113913a65a2ea8a1af94e1e12b4cbe32e13f7ac82e8defcb603339687977780e`. The manifest recorded 1,287 files before patch and 1,275 after patch.

The monitored repository suite passed: 2,061 passed, 11 skipped, 1 deselected, 2 warnings in 253.34 seconds. The wrapper reported `DISK_HYGIENE_PASS`, pytest peak 58,950,304 bytes, disposable peak 58,965,762 bytes, and 15,312 bytes of disposable PackLab files after cleanup. C: free bytes were 186,934,845,440 before the suite, 186,841,804,800 before wrapper cleanup, and 186,902,413,312 after cleanup. Ruff, Ruff format, mypy (236 source files), compileall, workflow YAML parsing, and `git diff --check` passed. The warning details and commands are in the Codex implementation log.

## Safety, provenance, and unverified acceptance gates

- Pushes did not start the native workflow; the native workflow is manual-only and exact-input gated. The ordinary Python Quality run remained enabled and passed on the implementation SHA.
- The owner Desktop checkout retained its same preexisting dirty/untracked status; no owner checkout or OwnerDev runtime files were edited or refreshed.
- No local native compilation, pywrap generation, opaque OCP wheel substitution, secret/private-data upload, signature, public release, or deployment occurred.
- The dispatched run produced no OCCT SDK checkpoint, official-source hosted patch output, compiled `OCP*.pyd`, runtime validation, package smoke, license/notice clearance, installer, or cache-hit evidence. OCP reported version/runtime identity was therefore not observed from a compiled runtime. No artifact SHA/size exists for native outputs.
- Engineering redistribution clearance is unproven; `legal_review_required=true`, `public_release_authorized=false`. No legal approval is claimed.
- Root `TASKS.md`, ChatGPT audit documents, and owner decision files remain ChatGPT-only and unchanged by this implementation pass.

## Required disposition

`BATCH_STOPPED_AT_PL-0350 / AWAITING_INDEPENDENT_AUDIT`
Stop code: `CAPACITY_PREFLIGHT_SETUP_PYTHON_VERSION_UNAVAILABLE`.

The next action is independent review of the implementation and this blocker evidence. This report does not authorize a retry, alternate toolchain, warm run, adjacent PL task, or acceptance claim.

SHA-256 of `PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md`: `b55ddf9fad652449e3c29db02b4f343976a4624e8d3e91748cf2e5fadc649c2e`.
