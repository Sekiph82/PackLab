# PL-0006-C002 - Codex Current-State Re-entry Work Order V01

Task: **PL-0006 - Define semantic versioning rules for PackLab Studio, PackLab Capture and PackScan schema.**

Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Canonical local workspace: `C:\Users\sekip\Desktop\PackLab`

## Why this cycle exists

PL-0006-C001/V01 produced the substantive versioning policy and the independent audit accepted the policy content but returned `CHANGES_REQUIRED` because the exact required pre-material synchronization command `git fetch origin main --prune` was not run at the required time.

A C001/V02 remediation work order was published, but it was never executed. No matching `CODEX_LOG_V02.md` or `CHATGPT_AUDIT_V02.md` exists.

This C002 cycle is a clean current-state re-entry from the actual GitHub `main` repository. It preserves all accepted PL-0006 work, revalidates the full policy strictly, repairs the missing synchronization-evidence requirement prospectively, and does not advance to PL-0007 unless ChatGPT later returns `AUDITED_PASS`.

## Canonical authority

GitHub `main` is repository truth:
https://github.com/Sekiph82/PackLab/tree/main

Root tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Agent instructions:
https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md

Audit policy:
https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_POLICY.md

Audit learnings:
https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_INDEX.md

Implementation guide:
https://github.com/Sekiph82/PackLab/blob/main/IMPLEMENTATION_GUIDE.md

PL-0006 V01 prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/PL-0006-C001/CODEX_PROMPT_V01.md

PL-0006 V01 strict criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/PL-0006-C001/CHATGPT_AUDIT_CRITERIA_V01.md

PL-0006 V01 Codex log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/PL-0006-C001/CODEX_LOG_V01.md

PL-0006 V01 independent audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/PL-0006-C001/CHATGPT_AUDIT_V01.md

Historical unexecuted C001/V02 prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/PL-0006-C001/CODEX_PROMPT_V02.md

Historical C001/V02 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/PL-0006-C001/CHATGPT_AUDIT_CRITERIA_V02.md

Accepted substantive policy:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/VERSIONING_POLICY.md

This work order:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/PL-0006-C002/CODEX_PROMPT_V01.md

Matching frozen criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/PL-0006-C002/CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization gate

Before material work, root `TASKS.md` must show:

- Current Task: PL-0006
- Current Task Status: CHANGES_REQUIRED
- Required Actor: CODEX
- Next Task/Action pointing to this C002 work order

If any of those statements are false, STOP and return `TASK_STATE_MISMATCH`.

Do not infer task authorization from unchecked rows. Use only the explicit Project Status block.

## Phase 0 - exact safe synchronization before any material validation

Run exactly in this order before editing or materially revalidating PL-0006:

```powershell
cd C:\Users\sekip\Desktop\PackLab
git rev-parse --show-toplevel
git remote -v
git status --porcelain
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
```

Required behavior:

1. Verify the Git root is exactly the PackLab checkout.
2. Verify `origin` resolves to `https://github.com/Sekiph82/PackLab.git`.
3. Historical untracked `.hiveai/` may exist locally but must never be staged or committed.
4. If any tracked local change exists, STOP and report it.
5. If local is ahead or diverged from `origin/main`, STOP and report it.
6. If local is behind-only, synchronize only with:

```powershell
git merge --ff-only origin/main
```

7. After any fast-forward, run:

```powershell
git rev-list --left-right --count HEAD...origin/main
git rev-parse HEAD
git rev-parse origin/main
git status --porcelain
```

8. Before material validation begins, prove:
   - ahead/behind is `0 0`;
   - local `HEAD` equals `origin/main`;
   - no tracked local changes exist.

Forbidden synchronization operations:

- `git reset`
- `git rebase`
- force-push
- destructive checkout
- silent stash
- `git clean`

## Objective

Strictly revalidate the existing accepted versioning policy against current repository truth and the full PL-0006 contract.

The existing policy is:

https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/VERSIONING_POLICY.md

Do not rewrite it merely to create a diff.

If no genuine substantive defect is found, leave it byte-identical.

If a genuine defect is found, document the defect first in the C002 log, make the smallest necessary correction, and fully re-run the affected checks.

## Full substantive revalidation

Revalidate all of the following, not just the previous synchronization defect.

### Version domains

Confirm the policy independently defines:

- `StudioVersion`
- `CaptureVersion`
- `PackScanSchemaVersion`

Confirm the three domains are related but not numerically locked.

Confirm task IDs and commit SHAs are not semantic versions.

### Studio and Capture SemVer behavior

Confirm MAJOR, MINOR, PATCH, prerelease, and development-stage `0.y.z` behavior remain explicit and internally consistent.

Confirm internal refactoring alone does not force MAJOR when public compatibility remains intact.

### PackScan schema semantics

Confirm:

- incompatible structural/semantic change maps to schema MAJOR;
- backward-compatible additive change maps to schema MINOR only when older readers can safely tolerate it;
- schema PATCH cannot silently alter required fields, units, coordinate systems, checksums, orientation, calibration, or required file meaning;
- documentation-only clarification rules distinguish PATCH from no schema bump.

### Compatibility matrix

Revalidate all required cases:

- older Studio reading newer schema;
- newer Studio reading older schema;
- older Capture output consumed by newer Studio;
- newer Capture output consumed by older Studio;
- unsupported future schema MAJOR;
- supported older schema MAJOR with migration;
- same MAJOR with higher MINOR;
- same MAJOR/MINOR with higher PATCH.

Compatibility must be declared and capability-checked, never guessed from numerical proximity.

### Reader and writer behavior

Confirm a future reader:

- rejects unsupported future MAJOR cleanly;
- does not silently reinterpret units, coordinate frames, checksum rules, photo orientation, calibration, or required file semantics;
- preserves immutable imported `.packscan` evidence.

Confirm a future writer:

- emits exactly one explicit schema version;
- cannot emit behavior beyond that declared schema version;
- does not pull deterministic writer implementation into PL-0006.

### Migration behavior

Confirm migrations are:

- explicit;
- versioned;
- source-version and target-version bound;
- non-destructive to source evidence;
- fail-safe against partial overwrite;
- not assumed reversible;
- explicit and audit-visible when lossy.

### Application-to-schema declarations

Confirm future Studio/Capture releases must declare:

- application version;
- schema read range;
- schema write version or versions;
- migration support range;
- known incompatibilities.

PL-0363 and PL-0364 must remain owners of coordinated release numbering and release-manifest implementation.

### Architecture boundaries

Confirm the policy preserves:

- immutable raw `.packscan` evidence;
- millimetres as canonical engineering units unless a future audited ADR changes that contract;
- explicit coordinate-system semantics;
- Scan Mesh, Scan Master, and Design Model separation;
- no rendering/UI layer becoming dimensional truth;
- public repository privacy and secrets rules;
- no release implementation pulled forward.

## Scope

If the policy is still correct, the only tracked file Codex may add is:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/PL-0006-C002/CODEX_LOG_V01.md

Do not modify:

https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md

https://github.com/Sekiph82/PackLab/blob/main/CLAUDE.md

https://github.com/Sekiph82/PackLab/blob/main/IMPLEMENTATION_GUIDE.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_POLICY.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_INDEX.md

Do not modify any previous prompt, criteria, log, or audit artifact.

Do not create application code, schema implementation, release manifests, version files, tags, releases, workflows, package manifests, lockfiles, or dependency changes.

Do not begin PL-0007.

## Validation

Run and record at minimum:

```powershell
git diff --check
git diff -- TASKS.md
git status --short --branch
```

Perform explicit content checks that cover every substantive section listed above.

Perform an exact changed-file review before commit.

Perform a public-repository privacy/security scan over any changed file.

If `docs/architecture/VERSIONING_POLICY.md` is unchanged, prove it is unchanged against the synchronized C002 validation base by blob identity or an exact Git diff.

## Required log

Create:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/PL-0006-C002/CODEX_LOG_V01.md

The log must contain:

- cycle ID `PL-0006-C002`;
- links to this prompt and matching criteria using the full GitHub URLs;
- synchronized starting commit;
- exact Phase 0 commands and raw results;
- explicit pre-merge ahead/behind relation;
- whether fast-forward was needed;
- final pre-validation `0 0` relation and equal HEAD/origin/main;
- files read;
- files changed;
- proof whether `VERSIONING_POLICY.md` remained unchanged;
- full substantive revalidation results;
- every validation command with expected result, failure condition, and actual result;
- failures and fixes;
- privacy/security review;
- protected-scope review;
- implementation/evidence commit and push result;
- remote visibility evidence;
- known limitations;
- final `AWAITING_AUDIT`.

Do not predeclare the future SHA of a commit that will contain the final version of this log.

## Commit and push discipline

If no policy defect exists:

1. add only `coordination/sessions/PL-0006-C002/CODEX_LOG_V01.md`;
2. commit it;
3. push normally to `origin/main`;
4. verify remote visibility;
5. return `AWAITING_AUDIT`;
6. stop.

If a genuine policy defect is found:

1. make only the minimal policy correction plus the C002 log;
2. document the defect and correction explicitly;
3. commit/push only those authorized changes;
4. return `AWAITING_AUDIT`;
5. stop.

Never edit `TASKS.md`. Never self-audit. Never start PL-0007.

## Final response

Return only:

- `PL-0006-C002`
- full GitHub URL to the published Codex log
- `AWAITING_AUDIT`

Then stop.
