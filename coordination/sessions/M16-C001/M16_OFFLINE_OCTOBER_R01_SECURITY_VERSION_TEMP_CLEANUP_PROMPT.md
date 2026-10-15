# PackLab October Offline R01 | PEM Guard + SemVer Fix + ALL Safe Task-Owned TEMP Cleanup

**EXPLICIT OWNER ORDER (2026-10-15):** Review the published October offline Codex log, finish narrow source issues without ANY GitHub Actions, and **inspect and delete every proven unnecessary temporary file/folder created by PackLab October offline work**. Do not interrupt other work or delete unverified/owner resources. Treat cleanup as a real required outcome, not merely a disk-size report.

## Read and understand first

- Independent ChatGPT static audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16_OFFLINE_OCTOBER_CHATGPT_AUDIT_V01.md
- Builder's previous truthful log: https://github.com/Sekiph82/PackLab/blob/offline/packlab-2026-10-no-actions/coordination/sessions/M16-C001/M16_OFFLINE_OCTOBER_CODEX_LOG_V01.md
- Zero Actions owner policy: https://github.com/Sekiph82/PackLab/blob/main/docs/development/NO_ACTIONS_OFFLINE_WORK_POLICY_2026-10-15.md
- Permanent worktree cleanup rule in root `AGENTS.md` and source-of-truth `TASKS.md` (ChatGPT-only).
- Work branch **`offline/packlab-2026-10-no-actions`**, expected starting commit `e4e4f984013bd85a6aa14482ded8239a103a92b5`. Confirm actual remote and fail on unexpected branch drift. Keep PRIVATE repository and main untouched by source/test changes. **NO PR**.

## P0: Absolute, non-negotiable zero-cost constraints

- **ZERO GitHub Actions** workflow dispatch/rerun/trigger, paid GitHub runners, paid Codespaces, alternative hosted CI, workflow edit, PR, or code/test push to `main`. Do not ask owner to pay or raise limits. Do not edit CI workflow files. Git branch offline source/test work only with no automatic Actions path triggers; check live workflow triggers BEFORE push.
- **No native build** or Installer/PyInstaller/OCCT/OCP rebuilding, no iOS Xcode simulator, no downloaded SDK/model, no `uv sync` with huge dependencies, no new credentials, no factory/public release. Reuse installed local CPython 3.12 for tiny stdlib tests. Avoid expensive disk writes.
- Do not edit root `TASKS.md`; ChatGPT alone manages canonical project state. Do not advance/claim full PL-0354 205-test acceptance, PL-0355+, M17, PL-0368 or legal rights.
- Protect owner's original `Desktop/PackLab`, `OwnerDev`, previous-good `PackLab.exe`, private retained Installer, OCCT/OCP/SDK/native checkpoints, any unique fixture/assets/evidence, other projects, active worktrees and global/shared caches.

## P1: Two real static-audit corrections

**F01: PEM/private-key bypass**
- Current `tools/ci/ci_data_safety.py` checks `SIGNING_TEXT_SUFFIXES`, but `.pem` and `.key` are not scanned, allowing e.g. a tracked `key.pem` with `-----BEGIN PRIVATE KEY-----` to pass the narrow `--check-signing-secrets` guard.
- **Extend scanner** for PEM and key files: recognize private-key PEM headers even when file suffix not in ordinary code/text suffixes, reject binary/undecodable private-key-looking payloads safely without echoing bytes/secret/path. Consider binary signing key extensions from current policy; do not erroneously treat a reviewed public-only certificate as a secret. Scope to tracked files only, not historical private-data excavation.
- Add small stdlib synthetic tests for PEM and .key private key, valid public certificate/no key, undecodable protected file (fail-closed), case-insensitive suffix, redacted report and existing nonsecret placeholders. Do not put actual keys into fixtures/logs.

**F02: False SemVer rejection**
- `tools/release/offline_version_inventory.py` currently accepts only one prerelease token and rejects valid `1.0.0-rc.1`/`0.2.0-alpha.2`, contrary to `docs/architecture/VERSIONING_POLICY.md` and adjacent draft validator.
- Correct strict SemVer to support dotted identifiers and build metadata, reject numeric prerelease leading zeros, empty segments, invalid chars and non-ASCII numbers; preserve source consistency and three independent versions. Add precise stdlib positive/negative tests. Do not change actual Studio/Capture/PackScan project version values.
- Ensure existing offline-release/changelog validators still return `PREPARATION` or `BLOCKED`, never `READY_FOR_RELEASE`. Review only for regressions attributable to the two narrow changes; avoid feature sprawl.

**Local checks only:** `python -B -m unittest tests.tools.test_offline_version_inventory tests.tools.test_offline_release_manifest tests.tools.test_offline_changelog tests.tools.test_ci_signing_data_safety`; `PYTHONDONTWRITEBYTECODE=1` or `-B` for scans; `git diff --check`; `python -B tools/ci/ci_data_safety.py --repository . --check-signing-secrets`; `python -B tools/release/offline_version_inventory.py`. Do NOT call hosted CI. If local Python doesn't exist, report exact blocker without package installation/download.

## P2: MANDATORY end-of-task TEMP cleanup (owner explicitly authorizes deletion of **proven disposable task-owned material**)

1. **Finish P1 FIRST**, execute tiny checks, commit/push implementation to PRIVATE **offline** branch, then commit append-only `coordination/sessions/M16-C001/M16_OFFLINE_OCTOBER_CODEX_LOG_R01.md` separately (also offline branch). Ensure `origin/offline/packlab-2026-10-no-actions` matches final published commit before cleanup. Do not delete a worktree still holding unique changes.
2. Measure actual available C: bytes **immediately before cleanup** using a Windows volume/free-space query; record time and original byte value. This is not proof of total task disk impact.
3. **Inventory BOUNDED PackLab-owned temporary locations only**: the exact R01/current October task worktree (if any); temporary/test directories and Python bytecode caches generated by the specific offline tools; explicit PackLab/R01/OCT-offline-named child directories under user `%TEMP%` or `%LOCALAPPDATA%\Temp` when exact creation provenance can be established; any one-off isolated test/fixture folder under PackLab worktree. Inspect `git worktree list --porcelain`, `git status --porcelain=v1 --untracked-files=all`, `git log origin/<branch>..HEAD`, ignored files, file creation/time association and process handles. **Do NOT sweep or recurse blindly through all AppData/TEMP.** No cleanup of unrelated `.codex` trees or agent caches by name association alone.
4. Classify EACH candidate path `PROVEN_DISPOSABLE`, `KEEP`, or `BLOCKED_UNKNOWN`. PROVEN_DISPOSABLE means definitely created by this PackLab offline task; no currently active process/editor/agent, no sole-copy source/tests/logs/SDK/Installer/evidence, no unpublished commits or unique tracked/untracked/ignored data, no owner changes, no symlink/reparse/junction, not a shared cache/environment or another project's folder. Ownership proof must be concrete; name/timestamp alone is insufficient. Treat existing R07 and PL0350/0352/0353 worktrees as protected unless independently proven disposable under a separate scope.
5. **Delete ALL PROVEN_DISPOSABLE** exact, bounded, task-owned TEMP targets using normal allowed OS operations (nonrecursive single-file removal; directories only when exact target tree is verified, no symlink/junction traversal). For Git worktrees use normal `git worktree remove <exact path>` from a stable parent checkout, **without `--force`**, and verify git metadata + directory absence. If policy approval blocks removal or files are locked, **STOP on that target**, do not bypass restrictions or use an alternative removal technique to evade policy. Continue only with separate unrelated individually safe targets.
6. Never run blanket `Remove-Item -Recurse C:\Users\...\AppData`, generic `%TEMP%` purge, `git clean -fdx`, `git reset --hard`, `git worktree prune`, global pip/uv caches cleanup, Windows storage cleaner, forced process kills, elevated policy override or deletion of owner's stable Desktop/PackLab checkout. Do NOT remove retained legacy worktree or Codex UI attachment marked `owned by another task`.
7. Measure actual C: free bytes **immediately after** cleanup. Provide **redacted per-target disposition** (exact verified task label or safe relative path, owner proof, size, deleted/preserved/blocked and reason); count of files/dirs removed, total logical size removed, measured free-space before/after, net bytes. Report `NO_SAFE_TEMP_RESIDUE_FOUND` if nothing removable exists. **Never claim all TEMP was purged, or that removing logical bytes equals free-space recovered.** If some candidates are blocked, report `TASK_TEMP_CLEANUP_PARTIAL` plus the exact blocker. There is no requirement to delete unknown/owner data merely to satisfy "all."

## P3: Truthful final handoff

- Publish the actual final offline-branch implementation and R01 Codex log before removing its own clean worktree. If physical cleanup occurs afterward, report post-cleanup measurements in user-facing handoff, and if possible safely append a *separate* short evidence-only GitHub commit without recreating a big local worktree or triggering Actions. Never falsify cleanup evidence in an earlier pre-clean log.
- Record all tiny local checks, test count, source commit, private branch parity, exact code differences, unchanged full 205-test blocked state and explicit `ZERO_ACTIONS_DISPATCHED`. If a cleanup approval is refused, preserve the file and report honestly.
- End `READY_FOR_INDEPENDENT_STATIC_AUDIT` only if both code corrections pass small local tests; cleanup status must be separately `DONE`, `NO_SAFE_TEMP_RESIDUE_FOUND` or `PARTIAL_BLOCKED`.
- November 1 is not automatic permission for paid CI; owner approval required before any billing or runner activity.

**Execute this R01 autonomously without paid CI and without destructive broad disk cleanup. Finish code publication, then delete every independently proven useless PackLab-offline task TEMP file, preserving everything else.**
