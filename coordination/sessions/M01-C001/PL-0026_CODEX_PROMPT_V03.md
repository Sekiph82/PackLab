# PL-0026 — Codex Remediation Work Order V03

Task: **PL-0026 — Cache/data override non-overlap remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CODEX_PROMPT_V03.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CODEX_LOG_V03.md

## Gate

Read AGENTS.md, TASKS.md, the blocking audit above, this prompt and its criteria. TASKS.md must authorize M01-REMEDIATION-BATCH-002 / CODEX.

Before material work:
```
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
git status --porcelain
```

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md. Do not start M02.

## Authorized files

- `core/src/packlab_core/cache_paths.py`
- `tests/core/test_cache_paths.py`
- `docs/development/CACHE_POLICY.md`

Use only minimal adjacent files if technically unavoidable and justify them in the log.

## Mandatory requirements

1. Preserve the corrected default Windows cache/work/data layout and existing macOS/Linux defaults.
2. Preserve PACKLAB_CACHE_ROOT and PACKLAB_DATA_ROOT overrides, but never silently accept an unsafe cache/data pair.
3. Reject with an actionable error when cache and durable data are equal, data is beneath cache, or cache is beneath data. Workspace may remain beneath cache.
4. Enforce the invariant in the public path-resolution flow used by PackLab, not only in documentation.
5. Add temporary-path tests for equal roots, both ancestor/descendant directions, safe siblings, defaults and overrides. No real profile paths.
6. Update CACHE_POLICY.md to describe the enforced non-overlap invariant.

## Validation

Re-run the still-valid original/V02 criteria, focused regression tests, full relevant M01 regression, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review, protected-file review and privacy/secrets review.

For unavailable native platform evidence, state the limitation rather than fabricating a pass.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CODEX_LOG_V03.md with synchronized start, implementation/evidence commit, exact files, defect mapping, commands/results, failures/fixes, scope/privacy, limitations and push evidence.

End with `AWAITING_AUDIT`. Do not self-audit.
