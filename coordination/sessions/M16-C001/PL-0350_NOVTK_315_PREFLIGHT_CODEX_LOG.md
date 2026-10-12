# PL-0350 315-Module no-VTK Preflight — Codex Log

Date: 2026-10-12
Actor: Codex implementation/preflight
Disposition: `AWAITING_INDEPENDENT_AUDIT / NATIVE_BUILD_OWNER_APPROVAL_REQUIRED`

## Revisions and synchronization

- Starting HEAD before sync: `19f9df681795506a7f62697804b1dbab5de8f9b2`.
- Fetched `origin/main`; it resolved to `da7fd2d94333dd964b163d924643eb0b476ebb0d`.
- Worktree branch: `codex/m16-r08-v16`; it was clean and six commits behind with no local commits ahead. Ran `git merge --ff-only origin/main`; fast-forward succeeded.
- Starting implementation revision: `da7fd2d94333dd964b163d924643eb0b476ebb0d`.
- Final revision: recorded after the docs-only commit below; push/readback verification follows in this log's publication section.
- User Desktop checkout `C:\Users\sekip\Desktop\PackLab` and other listed worktrees were not modified.

## Authority read

- `git show origin/main:TASKS.md` — live state authorizes exactly the 315-module PL-0350 preflight, identifies the owner decision, prohibits native builds/installer/PL-0351, and requires inspection of all workflow push triggers first.
- Read in full: `coordination/sessions/M16-C001/PL-0350_NOVTK_315_PREFLIGHT_CODEX_PROMPT.md`.
- Read in full: `coordination/sessions/M16-C001/PL-0350_NOVTK_315_PREFLIGHT_CHATGPT_AUDIT_CRITERIA.md`.
- Read in full: `coordination/sessions/M16-C001/PL-0350_OWNER_DECISION_NOVTK_315_MODULES.md`.
- Read prior evidence before source inspection: `PL-0350_UPSTREAM_GENERATED_SOURCE_READONLY_REPORT.md` and `PL-0350_UPSTREAM_GENERATED_SOURCE_CHATGPT_AUDIT_V01.md`.
- Read pinned inputs: `tools/packaging/windows_native_source_lock.json`, `tools/packaging/packlab-ocp-bindings-win.yml`, and `tools/packaging/packlab-ocp-bindings-win.lock`.

## Files changed

Only the two authorized report/evidence files:

- `coordination/sessions/M16-C001/PL-0350_NOVTK_315_PREFLIGHT_REPORT.md`
- `coordination/sessions/M16-C001/PL-0350_NOVTK_315_PREFLIGHT_CODEX_LOG.md`

No root `TASKS.md`, owner decision, audit, source, product, workflow, lock, cache, or runtime file changed.

## Checks and exact results

1. **Workflow push filters before edits** — `rg -n -A 18 '^\s*push:' .github/workflows`. Reviewed every `.github/workflows/*.yml`/`.yaml` file, including `_coordinator_pl0005_close.yml`, `packlab-preview-windows.yml`, `windows-python-quality.yml`, and `windows-studio-build.yml`. Result: both report/log paths are outside all push filters. No build or test workflow was dispatched.
2. **Source ZIP and 319-to-315 inventory** — streamed `https://github.com/CadQuery/OCP/releases/download/7.9.3.1.1/OCP_src_stubs_Windows.zip` with a Python `urllib.request`/`zipfile` script, maximum read `6,481,048` bytes, no extraction. Asserted exact 6,481,047-byte size and SHA-256 `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`; compared `.cpp`, `_pre.cpp`, and `_tmpl.hxx` ID sets; parsed `OCP.cpp` enum/module declarations and call sets; asserted all four sets equal the 319 source IDs; derived 315 after removing the exact four VTK IDs. Result: PASS; 319 triplets, 638 declarations, 638 calls, 315 retained IDs.
3. **Tiny malformed-input fixtures** — same in-memory script validated the actual ID list and rejected three malformed sequences: one missing ID, one extra ID, and one duplicate ID. Result: PASS; all three rejected. No production source was patched or compiled.
4. **Patch-plan digest** — canonical JSON was generated in memory from the exact ZIP SHA/size, sorted module IDs, exact removal set, sorted output IDs, triplet suffixes, and registration-pair rule. Result: SHA-256 `8263b11294f99be6052272273fb84b518abe328d43dc3d7ce668f86962584248`. It fingerprints the plan inputs/rules, not output source bytes.
5. **PackLab import scan** — `python -` scanned `.py` files in `core/src` and `apps/windows-studio/src` for literal OCP targets in normal imports and `importlib.import_module`/`__import__`. Result: 27 OCP submodules; all are retained IDs. The root literal `importlib.import_module("OCP")` was recorded separately. A broader source/test string scan found no references to `IVtk`, `IVtkOCC`, `IVtkTools`, or `IVtkVTK`. DXF export is the documented Python R2000 ASCII subset and has no OCP dependency. This is static source evidence only.
6. **Disk and scratch** — `Get-PSDrive C`: 173.60 GiB free before, 173.61 GiB after. ZIP streamed in memory; no scratch directory/file or extracted source tree was created. No private project data or credentials were accessed.
7. **Git safety** — before edits, `git status --short --branch` showed the managed worktree clean on `codex/m16-r08-v16`; only the prompt-authorized FF sync was applied. No reset, rebase, stash, cleanup, or checkout overwrite was used.

## Implementation and limitations

This was a static preflight and report-only change. The report records the actual archive inventory, import surface, patch-plan digest, version identity mapping, source-lock inputs, push-trigger boundary, and a proposed staged CI design. The proposed next patch would remove only four VTK module triplets and their declarations/calls, plus VTK discovery/link references. It has not been applied to the production ZIP files or integrated into PackLab.

Native build authorization remains absent. OCP C++ compile/link time and installed OCCT/OCP checkpoint sizes are unknown. The 79 opaque-wheel OCP native provenance rows, QtPdf/PDFium/Open3D notices, and final redistribution clearance remain open. No native runtime behavior, packaged smoke, or installer acceptance is claimed. `PL-0351` remains blocked; no milestone or task tracker status was changed.

## Secrets/privacy review

No secrets, credentials, Apple signing materials, private scans, supplier data, local caches/environments, generated reconstruction intermediates, or user runtime artifacts were staged. Only the two text reports above are intended for publication.

## Commit and push

- Initial report/log content commit: `0b479b115212c3e5fd8cdd6f952f8e75b3082928` (`docs(PL-0350): record no-VTK 315 preflight`).
- Report whitespace cleanup commit: `923d20484f8d9d9a1a7390f3a1e12f098ec2b9c2`.
- Publication evidence commit: `b288c322d33567cba597aa7edfe8e2da028319a4`.
- Ran `git push origin HEAD:main`; GitHub accepted `da7fd2d9..b288c322 HEAD -> main`. Fetched `origin main`; `git rev-parse HEAD` and `git rev-parse origin/main` both returned `b288c322d33567cba597aa7edfe8e2da028319a4`.
- All published commits touch only the two authorized report/log paths. The push filters were rechecked; no workflow dispatch or native-build trigger occurred. This final evidence update is another docs-only change to this log and will be pushed to `main` after `git diff --check`.
## Handoff

`PREFLIGHT_STATIC_CONTRACT_PASS / NATIVE_BUILD_NOT_AUTHORIZED`
`AWAITING_INDEPENDENT_AUDIT / NATIVE_BUILD_OWNER_APPROVAL_REQUIRED`
