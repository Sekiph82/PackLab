# PL-0353-R01 | CODEX REMEDIATION PROMPT | Guard Failure MUST Block Artifacts

**Task remains PL-0353. NOT a new milestone or acceptance of PL-0354.** Re-audit this exact independent finding first:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0353_CHATGPT_AUDIT_V01.md

**Already independently PASS:** Windows default Quality [38713322342](https://github.com/Sekiph82/PackLab/actions/runs/38713322342) (2,218 passed, 10 skip, 1 deselect, Ruff and mypy green); Preview [38712670742](https://github.com/Sekiph82/PackLab/actions/runs/38712670742) real EXE/setup, artifact guard and upload PASS. Do not rerun expensive product/native builds. The blocker is **security-critical workflow conditional logic**, not existing test failures.

## Exact bug

GitHub workflow YAML currently contains four new `if: always()` sensitive-data guard steps directly followed by `if: always()` artifact upload steps. A failed guard does **not** suppress a later upload with independent `always()`. Four verified pairs:

1. `.github/workflows/windows-studio-build.yml`: **Guard precompile diagnostic artifact inputs** -> **Upload noncompiling SDK and native runtime diagnostic evidence**.
2. Same: **Guard OCP quarantine artifact inputs** -> **Upload post-link OCP quarantine before any downstream failure can discard it**.
3. Same: **Guard packaged Studio smoke diagnostic inputs** -> **Upload packaged Studio smoke diagnostics**.
4. `.github/workflows/pl0350-fmt-dependency-probe.yml`: **Guard dependency probe artifact input** -> **Upload dependency probe evidence**.

**Fix:** give each guard an unambiguous unique `id`. Keep guard `if: always()` (diagnostics after earlier failure) when useful; change matching upload to `if: always() && steps.<guard_id>.outcome == 'success'` **plus** any necessary existing constraints, never just `if: always()`. Rejection, skip, missing guard or scanner failure MUST suppress upload, even if earlier job steps failed. Conversely, if an unrelated earlier stage fails and the guard independently succeeded on a legitimate diagnostic, the artifact may still upload safely. Do not alter names, retention category/period, SHA-pinned action, locked product configuration, native cache, installer provenance, or accepted binary.

**Extended audit:** inspect every workflow artifact-upload that uses `always()`, `failure()`, `cancelled()`, `continue-on-error`, `if-no-files-found: warn/ignore`, or another status override. Confirm no upload can bypass a data guard that applies to its exact payload. Where an upload is intentionally unconditional and contains only safe immutable reviewed evidence, document it precisely and justify. Guard failures should be clearly visible and should cause job failure, not silent success.

## Validation

- Add focused structured-YAML contract/negative tests to `tests/ci/` that map **step IDs** and assert each actual upload's `if` uses the exact preceding appropriate guard `.outcome == 'success'`. Tests must simulate or structurally reason the **rejection, skipped-guard, earlier-unrelated-failure and guard-success** outcomes. Do not rely on one unqualified substring check or parse YAML `on` incorrectly.
- Re-run only relevant locked pytest, Ruff/format/mypy/compile, YAML parser, `git diff --check`, and redacted data-safety scanner. A lightweight short hosted Windows Quality job may be run if necessary for workflow validation, but **NO OCCT/OCP native build, Installer recompilation, long workflow dispatch, owner Desktop operation or disk cleanup**.
- Non-destructively sync managed checkout with private `origin/main`. Keep root `TASKS.md` protected (ChatGPT-only), source binaries/asset provenance, existing owner worktree/OwnerDev and retained Installer `11959245441` untouched. Repo stays PRIVATE. No release, signing or factory rollout; legal review remains pending.
- Publish only minimal workflow/test fixes as an implementation commit, then append/finalize `coordination/sessions/M16-C001/PL-0353_CODEX_LOG_V02.md` in a separate log-only commit (or create V02-R01 append-only follow-up if old log cannot safely be appended; preserve old log). State four concrete conditional-fix pairs, checked remaining upload gates, tests and remote parity. **Do not modify ChatGPT audit**. End `READY_FOR_INDEPENDENT_AUDIT` only after correct security gates are proven; otherwise `BLOCKED_<EXACT_REASON>`.

**Start immediately; finish within this PL-0353 R01 cycle, without ordinary approvals.**
