# PL-0150 Codex Evidence Log V01

- Task: PL-0150 — Project portability check
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0150_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0150_CHATGPT_AUDIT_CRITERIA_V01.md
- Master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/MASTER_CODEX_PROMPT_V01.md
- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`

## Scope and synchronization

- Live `TASKS.md` authorized M06-BATCH-002 / READY / CODEX for PL-0150 through PL-0157; accepted PL-0135 through PL-0149, PL-0068 `OWNER_REQUIRED`, M03–M05, and M07 boundary were preserved.
- Starting commit: `acc33dd` (`acc33dd...origin/main` was `0 4`; clean checkout).
- Implementation/evidence commit: `24f4179619bdc0e937960e8cf750ff65582440cc`.
- No reset, rebase, force-push, destructive clean, or stash operation was used.

## Implementation

- Added `packlab_studio.portability.PortabilityScanner` and `scan_project_portability` as a read-only production seam.
- Reports classify required missing references, external-present references, regenerable derived/cache content, portable project-owned content, and unsafe links/traversal.
- Reports use stable redacted reference identifiers and relative record locations; absolute paths, secrets, and raw payloads are not included.
- The scanner validates layout/project metadata and JSON integrity, computes an aggregate raw-evidence digest for evidence, and never copies or rewrites project/raw files.
- Added `ProjectManager.portability_report()` as the existing project-authority entry point.

## Validation evidence

- `QT_QPA_PLATFORM=offscreen uv run --locked pytest tests/studio/test_portability.py -q` -> `4 passed`.
- `uv run --locked mypy apps/windows-studio/src/packlab_studio/portability.py apps/windows-studio/src/packlab_studio/project.py` -> passed.
- `uv run --locked pytest -q` -> `276 passed, 4 skipped, 1 deselected`, with two pre-existing duplicate-zip warnings.
- `uv run --locked python -m compileall -q apps/windows-studio/src/packlab_studio/portability.py` -> passed.
- `uv run --locked ruff check apps/windows-studio/src/packlab_studio/portability.py tests/studio/test_portability.py` and `git diff --check` -> passed after import-order correction.

## Negative / boundary / regression coverage

- Fully portable project with raw evidence preserves the raw digest and does not expose raw bytes.
- Present and missing absolute external assets are distinguished without copying the supplier directory.
- Traversal references are reported as unsafe; derived files are reported as regenerable.
- Closed-project calls fail through the existing `ProjectError` boundary.

## Security / privacy and scope review

- Secrets, signing material, private scans, supplier payloads, generated binaries, and caches were not committed.
- Root `TASKS.md`, ChatGPT audit/criteria artifacts, accepted M03–M05 work, and M07 were untouched.
- The implementation is a report/plan only; it does not silently copy, rewrite, or mutate external assets or raw evidence.

## Publication and limitations

- Implementation commit was pushed to `origin/main`; `git ls-remote origin refs/heads/main` matched `24f4179619bdc0e937960e8cf750ff65582440cc`.
- This is builder evidence only. Native owner acceptance, independent audit, and any physical/native/GPU claim remain outside this child.

## Handoff

Builder evidence only; independent ChatGPT audit remains required.

READY_FOR_INDEPENDENT_AUDIT
