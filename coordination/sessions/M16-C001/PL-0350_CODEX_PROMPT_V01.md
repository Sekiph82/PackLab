# PL-0350 - Codex Prompt V01

Task: **Versioned Windows EXE/installer with redistribution inventory**
Milestone: **M16 - CI/CD, Signing & Distribution**
Cycle: **M16-C001**

## M16 global rules

- Read live root TASKS.md, M15 final audit, M14 final audit, the dependency/license register, versioning policy, secrets policy, and exact predecessor prompt/criteria before implementation.
- Root TASKS.md lifecycle is ChatGPT-owned; Codex must not edit it.
- M16 owns CI/build/release engineering only. It must not alter domain authority or pull M17 acceptance work forward.
- GitHub Actions permissions must be least-privilege. PR/fork paths must not receive signing secrets.
- Build caches may contain only reproducible dependency/tool caches. Never cache secrets, private scans, owner data, mutable reconstruction outputs, checkpoints, signing material, or generated project/library state.
- No private/proprietary sample scan, supplier attachment, POVU production artwork, certificate, provisioning profile, private key or token may enter the public repository or uploaded public CI artifact.
- New build dependencies/tools must be version-pinned or otherwise reproducibly selected, have license/provenance review recorded, and update the dependency/license register where relevant.
- Windows distributable packaging has a HARD REDISTRIBUTION GATE: actual shipped PySide6/Qt, cadquery-ocp-novtk/OCP/OCCT, Open3D and other bundled native/runtime files must have a reviewed inventory and required license/notice texts. If this cannot be completed truthfully, stop at the owning child rather than publishing a release-ready installer claim.
- CI network access for dependency acquisition is allowed only through declared package/tool sources; shipped applications must not gain hidden runtime download behavior.
- Build/signing provenance must exclude secret values and ambient owner-local paths.
- Every executable child publishes implementation/evidence commit(s), then distinct child-log-only commit ending exactly READY_FOR_INDEPENDENT_AUDIT.
- Run YAML/static validation where applicable plus locked repository tests, Ruff/format/mypy/compile for changed Python, and exact workflow/build smoke feasible on the owning runner.
- M17+ implementation is unauthorized. PL-0368 is a future post-M17 release gate and must not be executed in the pre-M17 M16 batch.

## Required implementation

Produce a versioned PackLabStudio.exe and Inno Setup installer artifact from the PL-0349 production build.

Before calling the installer distributable, complete a file-level inventory of the actual staged bundle: Python runtime, PySide6/Qt DLLs/plugins, OCP/OCCT/OCP-proxy native files, Open3D/native dependencies and other shipped third-party components. Generate/package THIRD_PARTY_NOTICES plus required license/exception texts according to reviewed evidence. Update DEPENDENCY_LICENSE_REGISTER with exact build-time shipped inventory evidence.

The installer filename/version must derive from canonical Studio version and build revision. Installer must install only packaged application/runtime files, not owner data, private scans, checkpoints or external reconstruction engines.

HARD STOP: if required redistribution license/notice obligations for the actual bundle cannot be truthfully inventoried/satisfied, do not publish a release-ready installer claim. Record BATCH_STOPPED at this child.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M16-C001/PL-0350_CODEX_LOG_V01.md` in a distinct log-only commit. Record workflow/build commands, exact tool versions, artifact facts, compliance limits and remote parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
