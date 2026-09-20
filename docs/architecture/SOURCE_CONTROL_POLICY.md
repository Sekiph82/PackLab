# PackLab Source-Control Policy

## Purpose and authority

This document defines source-control conventions for PackLab. It is a policy
artifact, not a live task tracker, release manifest, branch-protection
configuration, or claim that a future workflow is already implemented.

GitHub `main` in `Sekiph82/PackLab` is the canonical integration truth. Local
checkouts are execution workspaces. Root [`TASKS.md`](../../TASKS.md) is the
only live project-status tracker; this document and other coordination files
must not become a competing current-task ledger.

The current owner-authorized AI workflow may execute directly on `main` when
the active prompt explicitly requires it. That workflow still requires a
freshness check, protected-file review, bounded commits, and push evidence.
Future branch and pull-request workflows are defined below as conventions;
they require their own authorized task and do not silently replace the
current workflow.

## Task and branch identity

Permanent `PL-xxxx` identifiers are workflow identifiers. They identify the
requested unit of work and its evidence history; they are not semantic
versions and must not be used as `StudioVersion`, `CaptureVersion`, or
`PackScanSchemaVersion` values. Versioning remains governed by
[`VERSIONING_POLICY.md`](VERSIONING_POLICY.md).

When a branch is authorized, its name must retain the permanent task ID and
use a short descriptive suffix:

```text
codex/PL-0027-engine-discovery
```

The cycle/version belongs in coordination artifact names, not as a substitute
for the task ID. A task branch must not silently combine unrelated PL IDs.
Direct-main execution is acceptable only when the governing prompt says so;
it does not relax scope, audit, or synchronization rules.

## Commit and pull-request conventions

Commit messages use a short conventional type, the permanent task ID, and an
imperative summary:

```text
docs(PL-0007): define source-control policy
```

Implementation/evidence and log publication should be distinguishable commits
when the prompt requires that boundary. A commit must describe what actually
changed; it must not claim an audit verdict or task closure.

When an authorized future branch/PR workflow is used, the PR title should
retain the task ID and describe the bounded outcome:

```text
[PL-0027] Add dependency capability discovery
```

The PR body should link the full prompt, criteria, relevant log, and any
reviewable evidence. PR naming is a future integration convention, not a
second source of task status. `TASKS.md` remains authoritative for lifecycle
state.

## File classes and generated-file policy

Every candidate file is classified before publication:

| Class | Meaning | Public-repository rule |
| --- | --- | --- |
| Source artifacts | Hand-authored or deliberately maintained policy, source, schema, test, documentation, or approved public fixture files | Commit only when authorized, reviewable, and covered by the task scope. |
| Regenerable intermediates | Reconstructible meshes, temporary exports, build products, previews, derived caches, and other repeatable processing output | Keep outside the public source tree by default. Commit only when a frozen task explicitly defines the output as a safe, reproducible fixture or evidence artifact. |
| Local caches | Dependency caches, virtual environments, IDE state, OS metadata, logs containing local paths, and tool caches | Never publish as project source. Concrete ignore rules are governed by their authorized task. |
| Safe fixtures | Small, redistribution-cleared, synthetic or public samples used to test a contract | Record provenance and redistribution permission; keep them visibly separate from private production data. |

Generated does not mean safe. A file is not publishable merely because a tool
created it, and deleting a generated file from the working tree does not erase
its history. Private scans, Kenya assets, supplier documents, proprietary
artwork, credentials, signing material, local environments, and ephemeral
reconstruction outputs are prohibited from public Git regardless of file
extension or generator.

## Git safety and synchronization

Normal sessions fetch `origin main`, inspect ahead/behind state and tracked
changes, and use fast-forward-only synchronization when the checkout is
clean and behind. Unexpected divergence, conflicting tracked work, or an
authorization mismatch is a stop condition. The owner’s explicit batch or
bootstrap prompt may define a narrower exception.

Force-push, reset, rebase, destructive checkout, broad cleanup, silent stash,
and equivalent history- or data-destroying shortcuts are forbidden unless an
explicit owner-authorized prompt names the exact operation and target. Never
use a destructive cleanup to hide scope, untracked owner work, or a failed
validation. Preserve untracked owner files and inspect collisions before any
authorized operation.

Before commit, review the exact changed-file set, protected files, privacy and
security boundary, and `git diff --check`. Push only the authorized scope and
verify the remote commit is visible on canonical `main`.

## Git LFS decision boundary

Concrete Git LFS configuration, attributes, migration, quota, and storage
policy are deferred to PL-0023. Until that task is authorized and audited,
this policy does not add LFS configuration or treat large files as safe by
default. PL-0023 must consider file size, binary diffability, provenance,
privacy, reproducibility, clone behavior, retention, and whether a file is a
public fixture or protected production evidence. LFS must not be used to make
private data public or to bypass the generated-file and secrets policies.

## Cross-references and ownership

- [`TASKS.md`](../../TASKS.md) is the sole live task/lifecycle tracker.
- [`AGENTS.md`](../../AGENTS.md) defines repository role ownership and safe
  execution rules.
- [`MILESTONE_BATCH_PROTOCOL.md`](../../coordination/MILESTONE_BATCH_PROTOCOL.md)
  governs explicitly authorized sequential milestone execution.
- [`VERSIONING_POLICY.md`](VERSIONING_POLICY.md) governs public version domains;
  task IDs in this policy are not semantic versions.

These links provide evidence and rules; none of this document’s sections may
be interpreted as current project status or as authorization for a future
task.

## Scope boundary

This policy creates conventions only. It does not configure branches, hooks,
PR automation, Git LFS, ignore files, CI, signing, or release tooling.
