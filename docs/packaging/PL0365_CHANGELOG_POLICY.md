# PL-0365 | Audited task changelog policy V1

## Purpose and status

`tools/release/offline_changelog.py` generates a deterministic **offline
preparation draft**. It is not a public changelog, release notice, M17
acceptance, or release authorization. No root `CHANGELOG.md`, tag, GitHub
Release, or V0.1 publication is created by this task. PL-0368 and its M17 gate
remain required before release publication.

## Entry eligibility

An entry is eligible only when all of these are true:

1. Its exact `PL-####` ID appears once in the root canonical `TASKS.md` and is
   checked complete there.
2. The entry cites the unique highest-version task-specific ChatGPT audit under
   `coordination/sessions/`; citing an older passing audit when a later audit
   exists rejects. The latest audit's final `Decision:` or `Verdict:` must be
   exactly `AUDITED_PASS` or a qualified `AUDITED_PASS_*` decision. A Codex log,
   builder statement, peer review, commit message, workflow title, or an
   unchecked task is not acceptance evidence.
3. The entry cites the matching curated human-authored fragment at
   `docs/packaging/release-notes/PL-####.md`; the fragment's first line is
   `Task-ID: PL-####` and the next metadata line is one `Category:` from the
   allowlist. The fragment category must match the entry category. Its full
   file SHA-256 must match the entry. The human summary and each known
   limitation must appear literally in that fragment.
4. The task ID is unique in the input. Unknown, unchecked, duplicate, or
   unaudited IDs reject the entire draft. Extra fields reject; commit messages
   are not a supported source.

The fragment is a reviewable note source, not a substitute for task acceptance.
Keep it concise and free of links, POSIX/Windows paths, private scans, supplier
information, credentials, signing data, and personal information. The
generator also rejects common private-path, email, key, and token patterns in
displayed text. For clarity and safety, slash-separated tokens are rejected in
summaries and limitations even when they may be ordinary shorthand.

## Input fields and ordering

The JSON input follows `schemas/release/changelog-input.schema.json`. Each
entry supplies a task ID, one category (`Added`, `Changed`, `Fixed`, or
`Security`), one summary, an optional list of explicit known limitations, the
accepted audit reference, the note-fragment reference, and the fragment SHA.
The milestone is derived from the task's owning `# Mxx - ...` section in
`TASKS.md`, never provided by arbitrary input.

Generated Markdown sorts milestones numerically, categories in the fixed order
above followed by `Known limitations`, and IDs numerically within each
category. It emits only IDs, curated summaries/limitations, and the exact
source commit, release-train ID, and independent Studio/Capture/PackScan
version tuple. Evidence paths and personal repository details are omitted from
the generated text. Current source versions are independent domains; no
numeric lockstep is inferred.

## Command and failure behavior

```powershell
uv run --locked python tools/release/offline_changelog.py <draft.json> `
  --repo . --output <path-outside-repository>/packlab-changelog-draft.md
```

The source checkout must be clean. The tool binds the exact `HEAD` commit to
the source-only release train from `offline_version_inventory.py`. It creates
the output file only after the entire draft validates. An invalid draft,
missing acceptance evidence, unsafe reference/text, dirty source checkout, or
invalid version identity exits `2`, prints stable error codes, and writes no
output. Output is fixed as `PREPARATION_ONLY_NOT_RELEASE_AUTHORIZATION` and
states that M17 / PL-0368 release authorization has not been granted.

No production changelog is checked in because this implementation does not
add retrospective note fragments or generate release copy for prior tasks.
Those require explicit curated fragments and their final acceptance evidence.
