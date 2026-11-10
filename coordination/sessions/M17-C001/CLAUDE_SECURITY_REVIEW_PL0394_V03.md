# PL-0394 Independent Security Re-Review — V03

Date: 2026-11-10. Reviewer: independent Claude Code security reviewer (did not write the audit or the
remediation). No repository, settings, artifact or workflow change was made; this report is the only file
created and is uncommitted. Only synthetic canaries were used; no secret value was printed.

## Scope

| Item | Value |
| --- | --- |
| Reviewed commit | `ef5eb681fcebfb4329ef245e1b41850e56d7d95b` (= local HEAD = `origin/main`, clean worktree) |
| Responds to | `CLAUDE_SECURITY_REVIEW_PL0394_V02.md` (CHANGES_REQUIRED: N1 fix + audit amendments) |
| Files reviewed | `tools/ci/ci_data_safety.py`, `tests/tools/test_ci_signing_data_safety.py`, `.github/workflows/windows-studio-build.yml`, `.gitignore`, `CLAUDE_SECURITY_AUDIT_PL0394_V02.md` (amended) |

## Commands and results

| # | Command | Result |
| --- | --- | --- |
| 1 | Synthetic probe harness (scratchpad) calling `scan_signing_material` on 44 one-line files | See N1 table. All 13 legitimate-reference probes PASS; Apple Team/Key ID, AKIA, `ghp_`/`gho_`/`github_pat_`/`glpat-`/`sk-`/`xox`, quoted hex, quoted base64, mixed-case alnum (quoted and unquoted) all DETECTED. |
| 2 | Same probes against the pre-fix guard (`git show ef5eb681^:tools/ci/ci_data_safety.py`) | The fix is a strict improvement: 8 shapes moved from pass to DETECT, none from DETECT to pass. |
| 3 | `python -m tools.ci.ci_data_safety --repository . --check-signing-secrets` / `--tracked` / `--check-workflows` / all three combined | `PACKLAB_CI_DATA_GUARD=PASS`, exit 0, in all four runs (no false positive from the tightened exemption over all tracked files). |
| 4 | `pytest -q tests/tools/test_ci_signing_data_safety.py tests/ci/test_ci_data_safety.py tests/ci/test_windows_studio_build_workflow.py tests/ci/test_artifact_upload_guard_conditions.py` | **87 passed** |
| 5 | `ruff check tools tests` | All checks passed |
| 6 | `mypy tools` | Success: no issues found in 52 source files |
| 7 | `grep '${{ … inputs.|github.event.|head_ref|title|body|message …}}'` over `.github/workflows/*.yml` | Only `env:` assignments (`windows-studio-build.yml:480`, `packlab-capture-macos.yml:284` choice input, `windows-python-quality.yml:111-113` SHAs/event name) and one action `with: run-id:` (`windows-studio-build.yml:574`, not a script). No free-text input interpolated into any `run:` script. |
| 8 | `git ls-files -ci --exclude-standard`; `git check-ignore --no-index` on `id_rsa`, `id_rsa.pub`, `sub/id_ed25519`, `*.der/.jks/.keystore/.ppk`, `.env.local`, `.env.production` | 0 tracked files ignored; all probe paths ignored; no tracked file matches the new patterns. |
| 9 | `gh run list --branch main --limit 6` / `gh run view` (read-only) | ef5eb681: Signing Material Guard run `42888098145` **success**; Windows Python Quality run `42888098053` **in_progress** at review end. |
| 10 | `gh api …/secret-scanning/alerts` (read-only) | 0 alerts (the synthetic `ghp_`/`AKIA` canaries in the test did not raise alerts). |

## Verification of the requested changes

**N1 — FIXED (with residuals, see P3-1).** `tools/ci/ci_data_safety.py:589-599` now tests the original-case
value. Exempt: (a) UPPER_SNAKE with at least one underscore (`:589`), (b) **unquoted** all-lower-case
identifier or dotted identifier not starting with a `TOKEN_PREFIXES` entry (`:119`, `:591-598`). Quoting now
always defeats (b), so quoted lower-case values are flagged. The new test
`tests/tools/test_ci_signing_data_safety.py:97-126` covers 5 leaking shapes and 3 references and passes.

Probe results (synthetic values; "name gap" = the variable name or line shape is outside `SECRET_ASSIGNMENT`
or the file is not content-scanned, a pre-existing N5-class scope limit, not an N1 regression):

| Shape | Result |
| --- | --- |
| Apple Team ID / Key ID (10 upper alnum), quoted `.py`, unquoted `.sh`, `x.env`, YAML | DETECTED |
| `AKIA…` quoted/unquoted; `ghp_` mixed and `gho_` lower-case unquoted; `github_pat_`; `glpat-`; `sk-`; `xoxb-` | DETECTED |
| Hex quoted; hex unquoted digit-first; base64 quoted/unquoted (with or without `+/=`); mixed-case alnum quoted/unquoted | DETECTED |
| **Unquoted all-lower-case letter-first** value in `.sh`/`.yml` (e.g. 40-char lower hex starting a-f, lower alnum, `sk_live_…` all-lower) | **NOT DETECTED** |
| **Unquoted dotted value** with letter-first segments and no `-` (JWT-like `eyJ….eyJ….sig`) | **NOT DETECTED** |
| Quoted all-caps value containing `_` | NOT DETECTED (disclosed in audit) |
| Value containing `TEST`; `.env`/`.env.local` files; `$env:X =` (ps1) and `let X =` (swift) line shapes; `AWS_SECRET_ACCESS_KEY`/`API_KEY` names | NOT DETECTED (name gap / N5 residual, pre-existing) |
| Legitimate: `"APPLE_API_TOKEN_ENV_NAME"`, `GITHUB_TOKEN_NAME`, `settings.github_token`, `api_token`, `os.environ[...]`, `os.environ.get(...)`, `${VAR}`, `$VAR`, `${{ secrets.X }}`, `<your-token>`, `PLACEHOLDER`, `None`, `example-token` | PASS (no false positive) |

**N4 — FIXED.** `PACKLAB_REUSE_OCP_RUN_ID` is set in the `env:` of job `controlled-ocp-runtime`
(`windows-studio-build.yml:462`, env at `:480`), the same job that contains both consumers (`:566`, `:634`),
which now read `$env:PACKLAB_REUSE_OCP_RUN_ID`. Step `if:` conditions (`:563`, `:568`, `:577`) use expression
context, not script text, which is safe. No remaining direct interpolation of free-text inputs into `run:`
scripts in any workflow.

**N5 — PARTLY FIXED, as the audit states.** `.gitignore:94-102` adds key/keystore shapes and `.env.*`; it
affects no tracked file. The scanner suffix sets (`ci_data_safety.py:87-114`) are unchanged.

**N8 — FIXED.** F2 heading and body, Boundaries and Post-audit action are now consistent: the artifact was
live when the audit ran and was later deleted (404). The un-auditable public download window is stated
explicitly (`AUDIT_V02.md:45-47`).

**N2, N3, N6, F4 — DISCLOSED, NOT CLAIMED FIXED.** N2 (commit e-mail, `:95-101`) and N3 (no branch
protection/rulesets, guard not required, SHA pinning unenforced, `:103-105`) are marked owner-only. N6
(wiki, private vulnerability reporting, `SECURITY.md`, `LICENSE`, `:115-116`) is marked owner/legal. F4
(Dependabot security updates, non-provider patterns, `:58-59`) is an owner recommendation. N7 is open.
TASKS.md keeps PL-0394 `[ ]` pending this review (`TASKS.md:781`), so nothing was falsely checked.

**F6 count — CORRECTED, pattern-dependent.** The audit now states 231 files (218 coordination). My recount at
ef5eb681: 227 files (216 coordination) for the backslash form `Users\<owner>`, and 285 (273) when forward-slash
and JSON-escaped forms are included (284/272 at `08ed55e2`). The impact statement (account name only) is
correct either way; see P3-3.

## Findings

No P0, P1 or P2.

**P3-1 (guard residual, audit under-discloses it).** `tools/ci/ci_data_safety.py:591-598` exempts any
**unquoted** value that is all lower-case letter-first, or dotted, regardless of file type. In `.sh`, `.yml`,
`.ini`, `.cfg`, `.properties` and `.toml`, an unquoted value is a literal, not a reference. About 37% of
lower-case hex tokens (first character a-f) and many JWT-shaped tokens therefore pass. GitHub push
protection does not cover generic hex or JWT values while non-provider patterns are off (F4), so "push
protection remains the backstop" does not apply to these shapes. The audit's N1 residual
(`AUDIT_V02.md:92-93`) names only the quoted all-caps case. Recommended follow-up (non-blocking):
- Apply the unquoted-identifier exemption only to code suffixes (`.py`, `.swift`), or require the
  lower-case identifier to contain `_` or no digits.
- Add `sk_` to `TOKEN_PREFIXES`.
- Add a letter-first lower hex canary to the test.
- Extend the audit N1 residual sentence to name these shapes.

**P3-2 (N5 residual under-stated).** `AUDIT_V02.md:112-113` names only extension-less files. Also residual:
- `.env.local` and other `.env.*` files are not scanned (suffix `.local`).
- `.der`, `.jks`, `.keystore`, `.ppk` and `.gpg` are not filename-blocked by the guard, so `.gitignore` alone
  does not stop `git add -f`.
- Generic names such as `AWS_SECRET_ACCESS_KEY` and `API_KEY` fall outside `SECRET_ASSIGNMENT`.
- `$env:`/`let` line prefixes are not matched.
- Any value containing `TEST` is skipped.

These are documented scope limits of a "not a general secret scanner" guard. Recommend listing them in one
sentence.

**P3-3 (doc precision).** For F6, the count mixes HEAD (231) with the `08ed55e2` scope (218). The number also
depends on the path form; including forward-slash and escaped forms gives about 284. State the pattern used,
or say "at least 231". F4/N6 omit that Dependabot **alerts** (not only security updates) are disabled. N3
omits the fork-approval setting (`first_time_contributors`). None of this changes any conclusion.

## Verdict for PL-0394

**PASS: `CLAUDE_PEER_AUDITED_PASS`-eligible for the automated audit and remediation scope**, conditional on
hosted Windows Python Quality run `42888098053` for ef5eb681 completing successfully. It was in progress at
review end, and the Signing Material Guard run `42888098145` succeeded.

Both V02 blocking items are closed:
- **N1:** the Apple Team/Key ID and token-prefix class is now detected, with a regression test, and there are
  no false positives across the full repository.
- **Audit amendments:** N2 disclosed, F6 corrected, N8 contradictions removed, N3–N7 listed.

N4 and the `.gitignore` additions are correct and safe. P3-1 to P3-3 are non-blocking follow-ups. P3-1 is the
most worthwhile: a small code change plus one sentence in the audit.

Owner-gated items stay open and must not be checked by this evidence:
- N2: commit e-mail and account privacy settings.
- N3: branch protection/rulesets, required checks, Actions SHA-pin policy, fork approval.
- N6: wiki, private vulnerability reporting, `SECURITY.md`, `LICENSE`.
- F4: Dependabot alerts and updates, non-provider secret patterns.
- N7: public unsigned preview and iOS artifacts.
- The legal/licence/release gates (PL-0393/PL-0368) and Apple signing.
