# PL-0354 | ADDENDUM V01 | Mandatory Post-Task PackLab Worktree Cleanup

**OWNER DIRECTIVE.** This is an **additive** instruction to the PL-0354 task ALREADY IN PROGRESS. Do not interrupt, restart or re-run PL-0354, or launch cleanup while any coding, build, CI verification, publishing or evidence work is active.

## Permanent rule for PackLab Codex tasks

Every PackLab Codex task that creates a **new local Git worktree on the owner's laptop** MUST remove that task-created worktree **after the task is fully finished and verified**, so completed Codex worktrees do not accumulate and consume C: storage. This applies to PL-0354 and all later PackLab tasks. **The persistent agent rule is now recorded in the repository root `AGENTS.md`, section `Mandatory Codex worktree lifecycle`.** This PL-0354 addendum supplies the current in-flight execution details. A separate root `TASKS.md` edit was blocked by a platform safety review; no tracker synchronization is claimed. Codex NEVER edits `TASKS.md`.

### Execution sequence: finish first, clean second

1. **FIRST finish PL-0354 normally:** coding, bounded tests, any hosted CI, implementation commit(s), separate Codex log-only commit, publish to private `origin/main`, verify remote parity. Do not clean while the active worktree, another agent, or a process needs it.
2. **THEN identify task-created worktree(s):** use `git worktree list --porcelain`, exact paths, and parent repository metadata; match only **PackLab** task-specific worktrees created/used by this Codex task, never a guessed path or another project's worktree.
3. **For EACH candidate, independently check**:
   - Its branch/commits are fully published to private `origin/main`; no unique unpushed commits or branches that still need merge.
   - No tracked edits, untracked owner work, unstaged/staged changes, or unresolved work using `git status --porcelain=v1 --untracked-files=all`, `git log origin/main..HEAD` / branch ancestry and branch metadata.
   - Inspect ignored/generated files too: no **unique** SDK/OCP checkpoints, Installer, last-known-good EXE, evidence, user assets, databases or settings exist only there. Generated disposable data must be reproducible and no longer needed; do not classify by folder name alone.
   - No running editor, Codex process, build, test, Git command or other agent uses that worktree; not protected owner `Desktop/PackLab`, `OwnerDev` or active/shared location.
   - No symlink/junction/reparse point that would extend deletion scope; never traverse an untrusted redirect.
4. **Remove only individually proven safe, clean, inactive, fully published PackLab worktrees** using normal `git -C <stable PackLab checkout> worktree remove <exact verified worktree path>` **without** `--force`. Exit the worktree as current directory before removal and use a stable parent checkout for the operation. Do not use recursive blanket deletion, `git clean -fdx`, `git reset --hard`, forced worktree removal or Windows policy bypass.
5. **Verify:** affected worktree is absent from `git worktree list --porcelain` and its exact directory has been removed; original checkout and private GitHub work remain unchanged. Record C: free bytes before/after and distinguish **actual net free-space change** from logical file lengths deleted. Do not claim recovered GB if C: free space did not increase.
6. **Legacy worktrees:** if there are old completed PackLab-only Codex worktrees, assess them individually under the SAME protections. The previously reported R07 worktrees included dirty and/or unmerged work and are **NOT preapproved for deletion**. Preserve anything ambiguous.
7. If any worktree cannot be verified/removable (dirty, untracked, ignored unique file, not merged, in use, tool approval/policy block), **DO NOT force/remove it**. Report `WORKTREE_CLEANUP_BLOCKED`, exact worktree identity (redact private absolute paths from GitHub/public logs), the concrete blocker, and the smallest owner decision required. Do not claim successful deletion. The engineering task's PASS/PENDING status must remain truthful and separate from cleanup outcome.
8. **Disk-safety:** no blanket AppData/TEMP/cache cleanup, no shared cache deletion, no deletion of unrelated projects, and no new heavyweight tests or downloads to justify removal. Preserve the retained production Installer artifact, Desktop owner files, OwnerDev, OCCT/OCP native checkpoints and the working app. No editing root `TASKS.md`.

## Required finish-line evidence

At the end of PL-0354, append a concise section **`Post-task PackLab worktree cleanup`** to its Codex log / handoff (publish the log before removing its own worktree, and report final external confirmation in the user-facing message). State: worktrees created, verified/removable, actually removed, skipped with why; before/after C: free bytes and actual net delta; `origin/main` publication confirmation; owner-originals untouched. A task that created no local worktree must say **`NO_LOCAL_WORKTREE_CREATED`**, not imply cleanup happened.

**Priority:** finish current PL-0354 task FIRST, perform its proven-safe worktree cleanup SECOND. This addendum does not authorize PL-0355, M17, binary rebuild, or any unrelated work.
