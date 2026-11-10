# PL-0394 Independent Security Review — V02

Date: 2026-11-10. Reviewer: independent Claude Code security reviewer. I did not write the audit or the
remediation. I made no repository, settings, artifact or workflow changes. The only file I created is this
report, which is uncommitted. No secret value was printed. Hits are shown as file plus a redacted prefix.

## Scope and SHAs

| Item | SHA / ref |
| --- | --- |
| Audited revision (audit V02) | `08ed55e244f229cf61a770ef5491f0fc5ed8237a` (3,882 tracked paths, 10 workflows) |
| Remediation commit | `2d2b686a3021e637e31f37ebd25a5cb5fe9252fd` |
| Local HEAD reviewed | `727bedbf7caf2b751777c5e8a438f3cca0fa46db` (clean worktree) |
| `origin/main` at review end | `e95879eafb4220153e1ca39022971059e211091c`: post-audit record of the F2 artifact deletion. I read it but did not check it out. |
| Other public refs | `codex/pl-0354-r01-recovery`, `offline/packlab-2026-10-no-actions` (both contained in main), `refs/pull/1/head` `53e5293b` (7 commits not reachable from any branch), `refs/pull/2/head` (in main) |

The inputs were the audit V02, the `2d2b686a` diff, the frozen criteria V01, the Codex log V01, all 9
workflows at HEAD (plus the deleted one), `tools/ci/ci_data_safety.py` and
`tools/ci/ci_signing_material_allowlist.json`.

## Commands and results

| # | Command (summary) | Result |
| --- | --- | --- |
| 1 | `git rev-list --objects --all`, then a filename filter (`p12 pfx pem key mobileprovision provisionprofile cer crt der keystore jks env packscan heic dng sqlite db ppk gpg asc kdbx ovpn keychain p8 xcarchive ipa`, `id_rsa`, `id_ed25519`, `secrets`, `credentials`, `.netrc`, `.npmrc`, `.pypirc`, `service account`) | **0 matches** in 23,523 objects. Also 0 `.packscan` paths. |
| 2 | Extension histogram over history and a list of binary/media paths | Only synthetic fixtures (`tests/fixtures/ci-safe-synthetic/*`, `tests/fixtures/m17_golden_subset/*` PNG/PLY), calibration SVGs and `PackLab.ico`. No photos, scans or archives. |
| 3 | Largest blobs in history (`git cat-file --batch-check`) | The largest is `IMPLEMENTATION_GUIDE.md` at 609 KB, then Swift tests (~315 KB) and synthetic PNGs (~305 KB). **No large binary blobs.** |
| 4 | Redacting scanner (scratchpad `histscan.py`) over the added lines of `git log --all -p`: AWS, GitHub, `sk-`/`sk-ant-`, Slack, Google, Stripe, JWT, Azure, npm/PyPI, PEM private key/certificate, `DEVELOPMENT_TEAM`, `AuthKey_*.p8`, credential assignments, basic-auth URLs, e-mails, KE/TR phone numbers | Provider tokens: **0**. Private key: 2 hits, both prose in the allowlisted M16 audit/prompt `.md`. Certificate: 1 hit, synthetic, in `tests/tools/test_ci_signing_data_safety.py`. Credential assignment: 1 dummy value in `tests/core/test_logging.py` (`api_ke***`). Phone hits: 8 false positives (PLY numbers, `uv.lock` hash). E-mails in content: only licence authors, `example.com`/`example.invalid` and `users.noreply.github.com`. |
| 5 | Same scan over the 7 unreachable commits of `refs/pull/1/head` | 0 token/key hits. The paths are only coordination markdown. |
| 6 | Commit metadata: `git log --all --format='%ae%n%ce'` | **6,662 author/committer fields carry the owner's personal address `sek***@hotmail.com`.** Others: 6 `act***@users.noreply.github.com` and 2 `nor***@github.com`. See N2. |
| 7 | Apple signing settings in `project.pbxproj` | Only `CODE_SIGN_STYLE = Automatic` and bundle IDs `com.packlab.capture(.tests)`. **No `DEVELOPMENT_TEAM`, no provisioning profile, no certificate identity.** |
| 8 | Kenya/supplier/customer markers (case-sensitive city names, `KES`/`KSh`, `Ltd/Limited/GmbH/PLC`, supplier fixture names) | 0 real hits. Supplier fixtures are synthetic (`Synthetic Supplier`, `Bottle Vendor`, `Ｆｏｏ Packaging`). `project-control/codex/owner-answers.jsonl` is 0 bytes. |
| 9 | Local Windows user paths (`C:\Users\<name>`) | 291 occurrences of the owner account name in **231 tracked files**: 219 under `coordination/` at HEAD (218 at `08ed55e2`), plus `AGENTS.md`, `CLAUDE.md`, `TASKS.md`, `handoff.md`, `tools/dev/post_task_safe_sync.ps1` and others. See F6. |
| 10 | `python -m tools.ci.ci_data_safety --repository . --tracked` | `PACKLAB_CI_DATA_GUARD=PASS` (exit 0) |
| 11 | `... --check-signing-secrets --check-workflows` | `PACKLAB_CI_DATA_GUARD=PASS` |
| 12 | Bypass probes of `scan_signing_material` on synthetic files in the scratchpad (deleted afterwards) | See N1. |
| 13 | `git ls-files -ci --exclude-standard`, path checks with `git check-ignore -v --no-index` | No tracked file now matches an ignore rule. `.env`, `.env.*`, `*.pem/.key/.p8/.p12/.mobileprovision`, `secrets/`, `/datasets/`, `/captures/` and `/dist/` are ignored. `tools/datasets/*` and `docs/datasets/*` remain trackable. `id_rsa` is **not** ignored. |
| 14 | `git grep _coordinator_pl0005` at HEAD | Only 3 historical prose mentions in coordination logs. No code, test or workflow reference. |
| 15 | `pytest tests/ci tests/tools/test_ci_signing_data_safety.py` | 351 passed, 5 skipped, 6 failed. All 6 failures are in `tests/ci/test_packlab_test_runner_behavior.py`: the local `taskkill` failed to terminate a child process tree. This is environmental and unrelated to `.gitignore` or workflow deletion. Hosted CI for `727bedbf` passed: Windows Python Quality run `42885936327` and Signing Material Guard run `42885936264` both succeeded. |
| 16 | `gh api repos/Sekiph82/PackLab` (read-only) | Visibility `public`, `allow_forking` true, `has_wiki` true. Secret scanning on; push protection on. Non-provider patterns, validity checks and Dependabot security updates off. |
| 17 | `gh api .../secret-scanning/alerts`, `.../dependabot/alerts`, `.../code-scanning/alerts` | 0 secret-scanning alerts. Dependabot alerts are **disabled** (403). No code-scanning analysis. |
| 18 | `gh api .../branches/main/protection`, `.../rulesets` | **Branch not protected (404). 0 rulesets.** |
| 19 | `gh api .../actions/permissions`, `.../workflow`, `.../fork-pr-contributor-approval`, `.../private-vulnerability-reporting` | `allowed_actions: all`, `sha_pinning_required: false`; default token `read`, cannot approve PRs. Fork approval is `first_time_contributors`. Private vulnerability reporting is `enabled: false`. |
| 20 | `gh api .../actions/artifacts` (names, sizes and expiry only; nothing downloaded) | First query: 4 artifacts, including `11959245441` `packlab-internal-installer-candidate-pl0350-warm-452fe893…`, 877,601,969 bytes, expires 2026-12-14T08:38:33Z. Unauthenticated **metadata** GET returned HTTP 200. Second query: 3 artifacts, and `GET …/artifacts/11959245441` returns **404** (deleted by the owner decision recorded in `e95879ea`). The remaining iOS archives (2.2 MB and 5.4 MB) and the SPM log expire 2026-11-11T15:4x. |
| 21 | `gh api .../actions/runs` | The push of `2d2b686a`/`727bedbf` triggered only the Quality and Guard workflows (both succeeded). The deleted coordinator workflow did not run. |
| 22 | History of workflows (`git log --all -p -- .github/workflows`) | `pull_request_target` never used. `secrets.*` never used. `contents: write` was added 3 times, all in the deleted `_coordinator_pl0005_*`/`_pl0006_*` workflows. |

## Workflow review at HEAD (9 files)

- **Triggers:** `pull_request` (no `pull_request_target` or `workflow_run`) in `packlab-capture-macos.yml`,
  `packlab-signing-material-guard.yml` and `windows-python-quality.yml`. Everything else is `push` to main with
  path filters, or `workflow_dispatch`.
- **Permissions:** every workflow and job has `contents: read`; some also have `actions: read`. There is no
  `write` anywhere, and the repository default token is `read`.
- **Secrets:** none are referenced. `github.token` is used only with `download-artifact` in
  `windows-studio-build.yml`, which is dispatch-only.
- **Action pinning:** all actions are SHA-pinned (checkout, setup-python, setup-uv, setup-micromamba,
  cache, upload/download-artifact).
- **Caches:** `actions/cache` runs on PR in quality and capture-macos. Keys are the lock-file hash. PR-scoped
  caches cannot be read by `main` (GitHub ref isolation). The OCCT/OCP caches are dispatch-only.
- **Artifacts:** paths are under `runner.temp` or `dist/`, and no workspace `.git` is uploaded. Retention is
  1–14 days, except the PL-0352 bridge (60 days, dispatch-only).
- **Expression injection:** `${{ github.event.* }}` appears only via `env:` (SHAs) in
  `windows-python-quality.yml:111-112`. One dispatch-input interpolation is listed under N4.

## Findings

**N1 (P2, new, CHANGES_REQUIRED). The signing guard's secret-assignment check misses ordinary alphanumeric
secrets.** In `tools/ci/ci_data_safety.py:572-585`, the value is upper-cased (`marker = value.upper()`) and
then tested against the identifier pattern `[A-Z_][A-Z0-9_]*…`. That pattern is meant to skip references
such as `X = SOME_CONSTANT`. Because the test runs on the upper-cased copy, every secret made only of
`[A-Za-z0-9_]` and starting with a letter or `_` matches it and is skipped.

Probes on synthetic files in the scratchpad, results only:

| Probe value (redacted) | Result |
| --- | --- |
| `APPLE_API_KEY: zq8Xr***` | NOT DETECTED |
| `ghp_F***` | NOT DETECTED |
| `glpat***` | NOT DETECTED |
| `9zq8X***` (leading digit) | DETECTED |
| `zq8X-***` (contains `-`) | DETECTED |
| `Abc+d***` (contains `+`) | DETECTED |

Apple Team IDs and API Key IDs (10 uppercase alphanumerics starting with a letter) are exactly the
`TEAM_ID`/`KEY_ID` class the regex names, and the guard silently passes them. The tests at
`tests/tools/test_ci_signing_data_safety.py:72-121` only use the hyphenated canary
`SYNTHETIC-CANARY-NOT-A-CREDENTIAL`, so the gap is untested. The audit cites this guard as PASS evidence.

- **Fix:** test the original-case `value` against the identifier pattern, or require the upper-case form
  `value == marker`.
- **Test:** add an alphanumeric canary, such as a 10-character mixed-case or Team-ID-shaped value, and assert
  `DIRECT_SECRET_ASSIGNMENT`.
- **Mitigation:** GitHub push protection still covers provider tokens such as `ghp_`. History scan #4 found
  no real credential, so this is a control defect, not an exposure.

**N2 (P2, new, audit accuracy; the fix is owner-gated).** The audit says "No owner personal address". That
holds for the tree but not for the public repository. The owner's personal e-mail is in 6,662
author/committer fields across essentially all ~3,331 commits, including the unreachable `refs/pull/1/head`
commits. Anyone can read it via `git log` or the GitHub API. It cannot be removed without a history rewrite
plus GitHub support for PR refs, which I do not recommend.

- **Required:** the audit must disclose this.
- **Owner options:** switch git `user.email` to the GitHub noreply address, and enable "Keep my email
  private" and "Block command line pushes that expose my email". These are account settings, so owner only.

**N3 (P3).** `main` has no branch protection and no rulesets. Repository Actions policy allows all actions
and does not require SHA pinning. As a result:

- The Signing Material Guard is not a required check.
- A PR can edit `tools/ci/ci_data_safety.py` and run its own weakened copy.

Fork PRs need approval only for first-time contributors. Recommended (owner settings): a ruleset on `main`
requiring the Guard and Quality checks; "require approval for all outside collaborators";
`sha_pinning_required: true`, or limit allowed actions to GitHub plus `astral-sh` and `mamba-org`.

**N4 (P3).** `windows-studio-build.yml:565` and `:633` interpolate `${{ inputs.reuse_quarantined_ocp_run_id }}`
(free-text `workflow_dispatch` input) directly into `pwsh` script text. The equality guard on line 565 is
itself the injection point. Exploiting it needs dispatch rights, which means write access, so the impact is
low. Pass the value through `env:` and compare `$env:…`.

**N5 (P3).** Signing-guard coverage gaps:

- Extension-less files (`.env`, `id_rsa`) and `.env.local` are never content-scanned, because
  `Path('.env').suffix == ''` is not in `SIGNING_TEXT_SUFFIXES`.
- `.der`, `.jks`, `.keystore`, `.ppk` and `.gpg` are not in `SIGNING_MATERIAL_SUFFIXES`.
- The prefix list does not cover generic names such as `AWS_SECRET_ACCESS_KEY`.
- `"TEST" in marker` skips any value containing that substring.

`.gitignore` covers `.env*`, `*.pem` and `*.key`, but not `id_rsa`/`id_ed25519`, `*.jks` or `*.keystore`.
The module documents itself as "not a general secret scanner", so this is defence-in-depth. Recommend
adding the names and suffixes, and adding `id_rsa*`, `id_ed25519*`, `*.jks` and `*.keystore` to
`.gitignore`.

**N6 (P3).** Owner-settings hygiene for a public repository:

- The wiki is enabled. Public wikis may be editable by any signed-in user unless restricted. Disable it if
  unused.
- Private vulnerability reporting is off, and there is no `SECURITY.md`.
- Dependabot alerts are off, which is broader than the audit's "security updates disabled".
- There is no top-level `LICENSE`, so public code carries no grant. This is for the legal gate
  (PL-0393/PL-0368).

**N7 (P3).** `packlab-capture-macos.yml` checkouts (lines 57 and 288) lack `persist-credentials: false` while
running on `pull_request`. The token is read-only and nothing under `.git` is uploaded, so this is hygiene
only.

Separately, `packlab-preview-windows.yml` (on push to `preview/windows/**`) and the iOS workflows publish
unsigned binaries as 1-day public artifacts. This is the same release-exposure class as F2, with short
retention. The owner/legal gate should cover it.

**N8 (P3, doc consistency in `e95879ea`, outside the reviewed SHA).** The F2 heading says RESOLVED, but its
body still reads "is still live". The Boundaries section still says "no artifact was deleted" and "F2 stays
open". Reword these so the report is not self-contradictory. The public exposure window, from when the
repository became public until the 2026-11-10 deletion, cannot be audited: download logs are not available.
State that explicitly.

## Verification of audit findings

| ID | Verdict | Evidence |
| --- | --- | --- |
| F1 | **CONFIRMED** | The deleted file had `contents: write` and an unpinned `actions/checkout@v4`, and pushed `HEAD:main`. Its trigger was a push touching its own path only. The deletion breaks nothing: there are no code, test or workflow references, and hosted Quality and Guard passed at `727bedbf`. No write-privileged workflow remains, and all other actions are SHA-pinned. |
| F2 | **CONFIRMED, now remediated** | The artifact existed: 877,601,969 bytes, expiring 2026-12-14, with metadata publicly readable (HTTP 200 unauthenticated). `pl0352-private-installer-retention.yml:114` and `:371` assert `private is True` only at producer and verification time, so the later visibility flip silently exposed it. Owner deletion confirmed: GET returns 404. The iOS unsigned archives are confirmed, expiring 2026-11-11. |
| F3 | **CONFIRMED** (versions and scope; pip-audit not re-run, network) | `uv.lock` has cryptography 45.0.7, certifi 2026.7.22, pytest 8.4.2 and setuptools 84.0.0. In `pyproject.toml`, `cryptography` and `pytest` are in the `dev` group; `setuptools` is the build backend. `cryptography` is imported only by `tests/transfer/tls_test_material.py`. Runtime deps: `cadquery-ocp-novtk`, `open3d`, `PySide6-*`. |
| F4 | **CONFIRMED** | The settings match. Dependabot **alerts** are also disabled. |
| F5 | **CONFIRMED** | No tracked file is affected, and no negation is introduced. `secrets/` is unanchored, so it matches at any depth; that is intended and hides no tracked file. Mixed-case `.HeIc` relies on Windows `core.ignorecase`, and the guard's `ALWAYS_BLOCK_SUFFIXES` is case-folded, so this is acceptable. |
| F6 | **Impact CONFIRMED, count DISPUTED** | The disclosure is the account name only. The count is wrong: 218 `coordination/` files at `08ed55e2` (231 tracked files at HEAD) contain the path, not 77. Non-coordination files include `CLAUDE.md`, `AGENTS.md`, `TASKS.md` and `tools/dev/post_task_safe_sync.ps1`. |

The audit's other claims check out:

- **Scan claims:** 0 sensitive filenames in history; 0 credentials; 3 PEM/certificate prose or test hits;
  guard PASS.
- **Counts:** 3,882 paths and 3,333 commits are consistent: 3,335 commits under `--all` now, minus 2
  post-audit commits.

## Things the audit missed

- N1: guard bypass (P2).
- N2: personal e-mail in public commit metadata (P2).
- N3: no branch protection, rulesets or SHA-pin policy.
- N4: dispatch-input interpolation.
- N5: guard and ignore gaps.
- N6: wiki, vulnerability reporting, Dependabot alerts, missing LICENSE.
- N7: macOS checkout credentials and other public binary artifacts.
- The F6 count.

## Verdict for PL-0394

**CHANGES_REQUIRED.** The repository-state conclusion holds. I independently confirmed that history and
tree contain no credentials, Apple signing material, `.packscan`/raw captures, Kenya/supplier/customer data
or large binaries, and the remediation commit is correct and safe. Before PL-0394 can be
`CLAUDE_PEER_AUDITED_PASS` for its automated portion, two changes are required:

1. **N1:** fix the identifier-skip logic in `tools/ci/ci_data_safety.py` (around line 584) and add an
   alphanumeric-canary regression test. A one-line change plus one test.
2. **Amend the audit report:**
   - Disclose N2 as an owner-gated open item.
   - Correct the F6 count.
   - Fix the F2/Boundaries contradiction (N8).
   - List N3–N7 as recommendations or owner-gated items.

Owner-gated items stay open regardless and must not be checked by engineering evidence: branch
protection/rulesets, Actions policy, fork approval, wiki, private vulnerability reporting, Dependabot, and
the commit e-mail and account settings. The licence, legal and release gates (PL-0393/PL-0368) and Apple
signing stay open as well. A focused re-review of the N1 diff and the amended report is enough to move to
PASS.
