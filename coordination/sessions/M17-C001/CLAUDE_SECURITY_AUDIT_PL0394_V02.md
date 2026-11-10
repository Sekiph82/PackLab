# PL-0394 Security / Secrets Audit of the Public Repository — V02

Date: 2026-11-10. Auditor: Claude Code (implementer of the remediation, so this is **not** the independent
review). Supersedes the scope of `PL-0394_CODEX_LOG_V01.md`, which audited the older revision `db772e35`.

## Exact scope

- Public `origin/main` = local HEAD = `08ed55e244f229cf61a770ef5491f0fc5ed8237a`, with 3,882 tracked paths and
  3,333 commits reachable across all refs.
- Repository `Sekiph82/PackLab`: `visibility: public`, `allow_forking: true`.
- The remediation commit that follows this report is reviewed separately by the independent reviewer.

## Checks run (all offline/free; no secret value was printed)

| Check | Tool / method | Result |
| --- | --- | --- |
| Sensitive filenames ever committed (`.p12 .pfx .pem .key .mobileprovision .cer .keystore .jks .env .packscan .heic .dng .sqlite .db`, `id_rsa`, `secrets.*`, `credentials`) | `git rev-list --objects --all` with a filename filter | **0 objects in all history** |
| Provider tokens / private keys in all history (AWS `AKIA`, GitHub `ghp_/gho_/ghs_/github_pat_`, `sk-`, `sk-ant-`, Slack `xox*`, Google `AIza`, `BEGIN … PRIVATE KEY`, `BEGIN CERTIFICATE`) | `git log --all -p` with a regex; matches redacted before display | **0 credentials.** 3 hits are documentation and a synthetic test string (`SYNTHETIC_PUBLIC_CERTIFICATE`, review prose about the PEM guard) |
| Credential-like assignments in the current tree | `git grep` with a redacted regex | 2 hits, both test fixtures with dummy values (`tests/core/test_config.py`, `tests/core/test_logging.py`) |
| E-mail addresses in the tree | `git grep` | Third-party licence notices (OpenSSL, zlib, qhull, …), `example.invalid` test addresses and `actions@users.noreply.github.com`. No owner address in tracked **files**. However, the owner's personal address is in **commit metadata**; see N2. |
| Data-safety guard | `python -m tools.ci.ci_data_safety --repository . --tracked` | `PACKLAB_CI_DATA_GUARD=PASS` |
| GitHub security settings | `gh api repos/Sekiph82/PackLab` (read-only) | Secret scanning **enabled**; push protection **enabled**; non-provider patterns, validity checks and Dependabot security updates **disabled** |
| Workflows | Manual read of all 10 `.github/workflows/*.yml` | See F1/F4 |
| Live Actions artifacts | `gh api …/actions/artifacts` (read-only) | See F2 |
| Python dependencies | `pip-audit 2.9.0` (OSV) on the 87 pinned venv packages; only public package names and versions were sent | 10 advisories in 4 packages, **all dev/test-only** (F3) |

## Findings

**F1 (P2, fixed in the remediation commit).** `.github/workflows/_coordinator_pl0005_close.yml` was an
obsolete one-shot tracker workflow with `permissions: contents: write` and an unpinned `actions/checkout@v4`.
It pushed straight to `main`. Its trigger was limited to edits of its own file, and its expected tracker text
no longer exists, but it was dormant write-privileged automation with a mutable action tag. **Remediation:**
the workflow is removed. Git history keeps it as evidence. Every other workflow uses `contents: read` and
SHA-pinned actions.

**F2 (P1, RESOLVED 2026-11-10 by owner decision: artifact deleted).** The Actions artifact
`packlab-internal-installer-candidate-pl0350-warm-452fe893…` (877.6 MB, would have expired 2026-12-14) was
live when this audit ran. It has since been deleted; see *Post-audit action*.
Artifacts of a **public** repository can be downloaded by any signed-in GitHub user. The workflow and log
names (`pl0352-private-installer-retention`, `repository_private=true`) show this installer was meant to stay
private. It is an unsigned internal build that bundles third-party binaries (Qt, OpenCascade and others).
Public availability is therefore a de facto distribution before the legal/licence and release gates
(PL-0393/PL-0368). Accepted PL-0351/PL-0352 evidence references this artifact by ID and digest, so deleting
it traded release-exposure risk against reproducibility of that evidence, so it was put to the owner. The
installer workflow checked that the repository was private only at upload time; making the repository public
later exposed the artifact. GitHub provides no artifact download logs, so whether anyone downloaded it
during the public window **cannot be audited**.
Unsigned iOS simulator and device archives from the 2026-11-10 push are also public; they expire on
2026-11-11.

**F3 (P3, open).** `pip-audit` flags `cryptography 45.0.7` (7 advisories, fixed ≤ 50.0.0), `certifi 2026.7.22`,
`pytest 8.4.2` and `setuptools 84.0.0`. All four are dev/test or build tooling only: `cryptography` only
generates test TLS material in `tests/transfer/tls_test_material.py`. The runtime dependencies
(`cadquery-ocp-novtk`, `open3d`, `PySide6`) are not flagged. Recommended follow-up: raise the dev pins
(`cryptography>=48.0.1`, pytest 9, setuptools ≥ 84.1) and re-lock with CI verification. This is not done here,
to avoid an unverified lockfile change.

**F4 (P3, recommendation).** Enabling Dependabot security updates and non-provider secret-scanning patterns
would add coverage. These are repository security-setting changes reserved for the owner.

**F5 (P3, fixed).** `.gitignore` did not cover HEIC/DNG phone captures, `/datasets/`, `/captures/`, `/dist/`
or `secrets/`. The data-safety guard would still block unapproved binaries, but text files under `secrets/`
were not ignored. **Remediation:** these patterns were added. No tracked file is affected (verified with
`git ls-files`).

**F6 (P3, accepted).** 231 tracked files, 218 of them coordination logs, contain the local Windows path
`C:\Users\sekip\…`. (The first count of 77 was wrong; the independent review corrected it.) This
discloses only the local account name. The GitHub owner handle is already public. No action.

## Boundaries

- No legal, licence-compliance, Apple-signing, physical or release acceptance is claimed.
- No repository settings were changed. One artifact was deleted on the owner's explicit instruction (F2).
- Independent security review: `CLAUDE_SECURITY_REVIEW_PL0394_V02.md` (CHANGES_REQUIRED, now addressed below;
  a short re-review is needed).

## Post-audit action

- 2026-11-10: the owner answered "Delete it". Artifact `11959245441`
  (`packlab-internal-installer-candidate-pl0350-warm-452fe893…`, 877,601,969 bytes, sha256 `b976c7d4…3da4ac`,
  run `38707054365`) was deleted with `gh api -X DELETE`.
- A follow-up GET returns HTTP 404, and no `packlab-internal-installer*` artifact remains.
- The PL-0351/PL-0352 tracker lines record that their digest evidence remains but the binary is gone.

## Independent-review findings (`CLAUDE_SECURITY_REVIEW_PL0394_V02.md`) and disposition

**N1 (P2, fixed).** `tools/ci/ci_data_safety.py` upper-cased the value before testing whether it was a
constant name, so any secret made only of letters, digits and underscores (Apple Team/Key ID shapes, `ghp_…`,
`glpat…`) was exempt. The exemption is now case-sensitive. Only an UPPER_SNAKE name with an underscore, or an
unquoted lower-case or dotted identifier that does not start with a token prefix, is exempt. Regression test:
`test_alphanumeric_token_shapes_are_not_mistaken_for_constant_names`, covering 5 leaking shapes and 3
legitimate references. The full-repository guard still passes. Residual: a quoted all-caps secret that
contains an underscore would still be exempt.

**N2 (P2, OWNER-ONLY, disclosed).** The owner's personal e-mail address is the author/committer address on
essentially every public commit (about 6,662 entries). Removing it from history would require a force
rewrite of `main`, which is prohibited, and would not remove existing clones or caches. Owner-side
mitigation for **future** commits:
- set a GitHub `noreply` commit e-mail;
- enable "Block command line pushes that expose my email".
No repository change can fix this.

**N3 (P3, owner settings).** `main` has no branch protection or rulesets. The data-safety guard is not a
required check. Actions allows any action, and SHA pinning is not enforced (it is followed by convention).
These are recommendations to the owner.

**N4 (P3, fixed).** In `windows-studio-build.yml`, the free-text input `reuse_quarantined_ocp_run_id` was
interpolated directly into PowerShell. It is now passed through job `env` (`PACKLAB_REUSE_OCP_RUN_ID`). The
workflow tests and the YAML parse still pass.

**N5 (P3, partly fixed).** `.gitignore` now also covers `id_rsa*`, `id_ed25519*`, `id_ecdsa*`, `*.der`,
`*.jks`, `*.keystore`, `*.ppk` and `.env.*`; no tracked file is affected. Residual: the content scanner still
skips files with no extension. GitHub push protection remains the backstop.

**N6 (P3, owner).** The wiki is enabled, private vulnerability reporting is off, and there is no
`SECURITY.md` or top-level `LICENSE`. The licence choice is an owner/legal decision.

**N7 (P3, open).** `packlab-capture-macos.yml` checkouts lack `persist-credentials: false` (the token is
read-only, so this is hygiene). The preview and iOS workflows publish unsigned binaries as public 1-day
artifacts, the same risk class as F2. Restricting or removing those uploads needs a decision on the PL-0393
evidence workflow.

**N8 (P3, fixed).** The F2 and Boundaries wording that contradicted the deletion is corrected above.
