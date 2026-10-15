# PL-0354-R02 | CODEX HANDOFF AFTER GITHUB BILLING UNBLOCKED

**Task: PL-0354 remains OPEN. This prompt is CONDITIONAL:** do not execute until the OWNER has confirmed that GitHub Actions billing/payment/spending restriction is resolved. Do not attempt retries in a loop while billing is blocked.

## Authority and exact evidence

- Independent PL-0354 R01 audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0354_CHATGPT_AUDIT_V02.md
- R01 implementer log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0354_CODEX_LOG_V02.md
- Focused run **38767357450**: signed-out simulator build PASS; 25/25 original previously failed methods PASS, zero skipped, source `ce422ebfda4b016d476386d16450e8004c59e090`. No app/test Swift changes to final source except ONE subsequent workflow selector-initialization change.
- **Exact final implementation SHA** `4b1cf5168c6a2c461e4b31735763393c5ea0f53c`.
- **Canonical full-run attempt 38770566255** had NO allocated runner (GitHub billing/limit block), zero steps. An earlier full-suite run on previous source had 205 total, 173 pass, 32 fail. NONE of these is a full R01 pass.
- The repo is **PRIVATE** and `TASKS.md` is ChatGPT-only.

## Execute only after owner says Actions available

1. Read current `origin/main`, task policy, independent R01 audit and GitHub Actions status; verify existing workflow `.github/workflows/packlab-capture-macos.yml` default `all` mode remains equivalent to exact R01 code, and no Swift source or tests changed since implementation `4b1cf516...`. If significant source drift occurs, stop and report the blocker, do not silently certify a different revision.
2. Use **one bounded genuine hosted macOS job** with no laptop worktree by preference: best is **Re-run all jobs** on exact blocked run https://github.com/Sekiph82/PackLab/actions/runs/38770566255, which ties proof to `4b1cf516...`. Alternatively a single authenticated `workflow_dispatch` of `PackLab Capture macOS CI` with input `focused_group=all` on verified equivalent source. Do not rebuild Windows Installer/OCCT/OCP or trigger other costly jobs. Do not modify billing or payment/account spending settings.
3. Verify real allocated `macos-15` runner, exact Xcode 16/iOS 18/iPhone 16 Simulator, NextLevel 0.19.1, `CODE_SIGNING_ALLOWED=NO`, app build and real `xcodebuild test`. Exact acceptance: xcresult `result=Passed`; `totalTestCount=205`, `passedTests=205`, `failedTests=0`, `skippedTests=0`; every required job step success. No `-only-testing` selector in `all` mode, no test filtering/skipping, no `continue-on-error`, no assertion changes or unapproved runner environment substitution.
4. When fully green, append result and immutable run/job/source IDs to a distinct `coordination/sessions/M16-C001/PL-0354_CODEX_LOG_V03.md` (or V02-R02 addendum if required to preserve historical log); publish log-only evidence on private main; report `READY_FOR_INDEPENDENT_AUDIT`. Do **NOT** edit root `TASKS.md` or ChatGPT audit, self-approve PL0354, or open PL0355.
5. If the full 205 suite runs and fails, capture actual failures, test count and root cause evidence, report `PARTIAL_XCTEST_FAILURES_REMAIN`. Do not reclassify targeted 25/25 as complete success. One narrow follow-up may be recommended only after ChatGPT audit; do not enter repeated paid CI loops.
6. If GitHub rejects again before runner allocation, stop without another retry and report `BLOCKED_HOSTED_CI_BILLING`, new run ID and exact annotation. Owner alone resolves payment/spending limits. There is no alternative artificially green build.
7. **Mandatory PackLab worktree lifecycle:** If you create a task worktree, finish/publish then safely remove only its own clean, fully merged, inactive worktree via ordinary `git worktree remove` without force; verify and record actual C: before/after free bytes, protect older dirty or unique ignored-data worktrees and owner Desktop/OwnerDev. If this task is GitHub-only and creates NO local worktree, report `NO_LOCAL_WORKTREE_CREATED`. Do not archive/remove stale Codex app attachments owned by other tasks or bypass UI policy.
8. Preserve private retained Windows Installer `11959245441` (expiry 2026-12-14 08:38:33 UTC) and source/rights evidence. No public release, signing, factory rollout, data leaks, hardware purchase or M17 development. `legal_review_required=true`; `public_release_authorized=false`.

**Do not start until the owner explicitly confirms billing is resolved. Then execute PL-0354 R02 once.**
