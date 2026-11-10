# PL-0438 Codex Prompt V01

## Owner authorization

On 2026-10-22 the owner delegated PackLab task sequencing, implementation, local validation, and maintenance of PackLab task/governance files to Codex. The owner directed that work remain within `C:\Users\sekip\Desktop\PackLab`. This prompt is strictly PackLab-local.

## Objective

Implement PackLab's autonomous task-queue behavior using root `TASKS.md` as the sole live task-state source. Codex must continue through eligible PackLab work without waiting for routine prompts, review turns, or stale sequencing-only stop text. Preserve genuine blockers and safety constraints.

## Frozen scope

1. Add a read-only queue validator in `tools/codex/task_queue.py`. It must consume the explicit `## Project Status` fields and the canonical `## Tasks` list, validate a permanent task ID, exact task title, state marker, unique task IDs, PackLab repository, and authorized branch. It must never infer the current task by choosing the first unchecked row and must never mutate `TASKS.md`.
2. Add bounded local tests in `tests/ci/test_codex_task_queue.py` for valid PackLab task IDs, supported dotted IDs in historical/shared data, current-task mismatch, status mismatch, duplicate IDs, malformed task rows, and multiple in-progress tasks.
3. Maintain one job metadata record at `project-control/codex/jobs/PL-0438/job.json`, linking the task to its prompt, log, validation command, and current handoff state. Do not add another live task/progress ledger.
4. Update PackLab `TASKS.md`, `AGENTS.md`, and PackLab coordination policy as needed to reflect the owner's current delegation and resolve contradictory historical sequencing instructions. Historical audit findings and authorship are immutable. Stop/wait language is not a gate when it only sequences work or requests a routine review/prompt. Genuine owner, safety, legal, security, licensing, physical/device, environment, conflicting-authority, or resource gates remain binding.
5. Keep all implementation and governance changes inside the PackLab repository. Do not inspect, edit, test, or clean another project. The existing shared Codex dashboard source is outside this repository and explicitly excluded. Do not create a substitute project dashboard as part of this task.
6. Configure a quiet local heartbeat only if a PackLab queue automation does not already exist, using the Codex automation tool. Do not hand-edit automation configuration; do not change another project's automation. It must inspect PackLab's explicit current task, avoid duplicate work, and notify only for material progress, a genuine blocker, completion, or required owner action.
7. Keep PL-0354 open until the real full 205-case iOS XCTest run occurs on supported macOS with Xcode. Do not represent Windows checks as XCTest. No GitHub Actions, paid CI, PR, native OCCT/OCP or Installer build, public/factory release, destructive cleanup, or TASKS history rewriting.
8. Run the small local tests requested above. Write `coordination/sessions/M16-C002/PL-0438_CODEX_LOG_V01.md` with starting/final commits, synchronization, files changed, exact commands/results, failures/fixes, negative coverage, limitations, privacy review, and truthful publication/handoff state.
9. Do not create an independent-review verdict or claim independent review. The owner delegated implementation and task authority to Codex; this does not turn local validation into hosted, device, release, or third-party review evidence.

## Validation

From the PackLab root, run:

```powershell
python -m pytest -q tests/ci/test_codex_task_queue.py
python tools/codex/task_queue.py --json
```

Expected: all focused tests pass; the CLI emits the explicitly identified PackLab current task and exits zero. During PL-0438 implementation the current ID was PL-0438; after its local completion the tracker advances to the real PL-0354 blocker. Any malformed or contradictory task state must produce a nonzero validation result without modifying repository files.

## Handoff

Record actual branch, commit, remote parity, and publication state in the log. Do not push a change that can trigger CI. Continue autonomous PackLab work after PL-0438 only when it is complete and the canonical tracker identifies an eligible next task. Otherwise record the concrete genuine blocker in `TASKS.md` and the log. Do not wait for routine review.
