# PackLab M16 | ONE-SHOT CODEX | ZERO GITHUB ACTIONS OCTOBER WORK

**OWNER DECISION 2026-10-15:** The owner reported **USD 56.92/week GitHub Actions spend** and explicitly forbids additional GitHub Actions charges. The owner nevertheless authorizes PackLab development that **does not use GitHub Actions** until November, without an automatic restart in November. This prompt is the exact scope of that offline work. **Never start a GitHub Actions workflow, rerun or retry a run, create a pull request, edit account billing or enable another paid CI.**

## Canonical facts and isolation

- Private repository `Sekiph82/PackLab`, normal `main` project state remains **PL-0354 AWAITING FULL 205 XTEST**, externally GitHub-billing blocked.
- **Dedicated remote branch already created:** `offline/packlab-2026-10-no-actions`, based on safe docs-only main commit `8f9db8e18c80f3621c98f0efd4e67a8a15308f3e`. DO NOT push offline source/code changes to `main` or create a PR while moratorium lasts. Check the exact branch before EVERY push and check live triggers. Existing relevant CI push triggers for code are main-only, and no PR is permitted; note other workflows and stop if branch trigger graph changes.
- Read `AGENTS.md`, ChatGPT-owned `TASKS.md`, `docs/development/NO_ACTIONS_OFFLINE_WORK_POLICY_2026-10-15.md`, `docs/architecture/VERSIONING_POLICY.md`, `docs/security/SECRETS_POLICY.md`, `docs/packscan/container-layout.md` and reviewed drafts in `docs/packaging/`.
- The three released-contract domains are independent: Studio 0.1.0 in `pyproject.toml` and `packlab_studio.__version__` at current source, Capture 0.1.0 build 1 in `apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj`, and PackScan schema `1.0.0` in `schemas/packscan/manifest.schema.json`. Source values are DEVELOPMENT identities, not shipping authorization.
- The current latest audited full run `38755083949` was 173/205 PASS on OLD code. Latest focused `38767357450` was 25/25 PASS. A new `all` run at final SHA `4b1cf516...` was **never executed** due billing. Do not self-approve PL0354 or start iOS/test/release/deployment work.
- Root `TASKS.md` is ChatGPT-only. Your implementation on `offline/packlab-2026-10-no-actions` is **PREPARATION, NOT ACCEPTED PL0355+ TASK CLOSURE**. Name commit/logs accordingly, avoid making M16 appear complete.

## Allowed actual October implementation, in order and without CI

**OFF-A01: Read-only & reproducible version inventory, aligned with future PL-0363.** Implement the smallest pure-stdlib Python tool (e.g. `tools/release/offline_version_inventory.py`) and bounded deterministic tests on synthetic inputs that parse/validate:
- Studio version from checked-in `pyproject.toml` and `apps/windows-studio/src/packlab_studio/__init__.py`;
- Capture version/build and bundle ID from checked-in `apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj` plus `Info.plist`;
- PackScan exact schema const from `schemas/packscan/manifest.schema.json`;
- Python/SemVer strict version and cross-file consistency; three versions are independent; no release tag, immutable artifact SHA or release-ready status invented.
Output MUST be labeled `OFFLINE_UNVERIFIED_BUILD`, contain source-relative paths only, no sensitive local absolute paths, and not claim execution of Xcode/app. Handle absent/unexpected/ambiguous version sources by fail-closed error.

**OFF-A02: Draft release manifest schema / fail-closed validation, aligned with future PL-0364/0366.** Build a deterministic local validator for **input release-candidate descriptions only**, requiring actual source SHA, all artifact digest/provenance IDs, version triad, declared PackScan read/write support, license notices, and independent accepted audits. Any missing field, PL0354 unaccepted, M17 not accepted, missing signatures for a signed release, or inconsistent artifact/source/provenance MUST return a clear BLOCKED result, not a released binary/tag. Generate no real candidate or installer.

**OFF-A03: Deterministic draft changelog policy and tests, aligned with future PL-0365.** Only independently accepted PL IDs may appear in release-ready notes; validate against reviewed source fragments/approved audit citations. Detect unknown, duplicate, unaccepted IDs and arbitrary commit-message inference. This tooling is offline PREPARATION only.

**OFF-A04: Static confidential data and Apple signing-secret audit, aligned with future PL-0360.** Extend a narrow **stdlib-only / no-network** scan of tracked source for prohibited signing/private material filenames, sensitive private-key headers and direct secret assignments with redacted output. Read existing `tools/ci/ci_data_safety.py` first; **reuse** rather than duplicate controls. No actual secrets or customer data; only unmistakably synthetic negative canaries. DO NOT print any detected secret material, touch repository history or delete files. Do not add GH workflow integration now.

**OFF-A05: Review and improve prepared docs**:
- `docs/packaging/PL0362_PL0367_OFFLINE_INSTALL_ROLLBACK_PREPARATION.md`
- `docs/packaging/M16_OFFLINE_RELEASE_CONTROL_PREPARATION.md`
Fix only provable source/documentation inconsistencies; ensure rollback never alters immutable original `.packscan`, iPhone physical installation requires signing, M17/legal remain blocking.

Do not implement PL0355/0356/0357 hosted workflow caching/runners, PL0358 signing or physical Apple install now. Do not touch iOS product source or release binary. Do not modify workflow trigger files, `apps/ios-capture/**`, `.github/workflows/**`, installers, OCCT/OCP/SDK checkpoints, AppData/OwnerDev, original Desktop or other projects.

## Absolutely ZERO Actions, ZERO new paid tools

- No `gh workflow run`, `gh run rerun`, Actions API dispatch, PR creation, push to `main` of code/test paths, hosted Windows/macOS runner, Codespaces paid machine, remote CI SaaS, cloud tests, signing, or external file upload.
- No `uv sync` of heavy dependencies, no OCCT/OCP/PyInstaller native builds, no full pytest, no macOS on Windows emulation; allow tiny local `python -m unittest` / targeted stdlib tests and `python -m compileall` plus diff checks. Max bounded runtime and no >100MB new local transient state. No speculative downloaded SDKs.
- Use **one** task worktree if needed; after ALL implementation and evidence have been safely published to the correct PRIVATE OFFLINE BRANCH and no local data remains unique, remove it using nonforced `git worktree remove` per root `AGENTS.md`. Older worktrees are NOT presumed safe. Record actual before/after C: free bytes and remove result.

## Handoff and audit discipline

- On the isolated `offline/packlab-2026-10-no-actions` branch, commit each bounded actual source/test implementation with truthful local-only provenance. Never merge to main automatically; no PR. Persist a single log `coordination/sessions/M16-C001/M16_OFFLINE_OCTOBER_CODEX_LOG_V01.md` describing what was done, actual local test counts, source SHA, no CI run, branch status, data budget and cleanup. `PASS_LOCAL_STATIC_ONLY` is allowed, `AUDITED_PASS` / `RELEASE_READY` is not.
- If an instruction would require any GitHub Actions or monetary activity, **STOP that step and report `DEFERRED_NO_ACTIONS`**, continue with independent offline-safe subtasks as appropriate. No request for billing activation.
- After work, do not claim the existing 205 XCTest is resolved, PL0354 accepted, any later PL completed or artifact/installer validated. GitHub default main and lifecycle remain frozen.
- **Stay within owner's October authorization and stop on owner command. Do not automatically resume in November or create background schedules.**

**Start OFF-A01 and continue sequentially through OFF-A05 without unnecessary questions. Execute locally/offline with zero Actions, and report actual work before concluding.**
