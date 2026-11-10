---
coordinationSchema: packlab-coordination/v1
artifactType: claude-implementation-log
cycleId: M17-C001
version: 01
actor: CLAUDE_CODE
status: IMPLEMENTED_REVIEW_PENDING
tasks: [PL-0384]
---

# Claude Implementation Log V01 — PL-0384 project migration across schema/app versions

Codex `PL-0384_CODEX_LOG_V01.md` was BLOCKED for lack of a real predecessor format. Git history has one:
before `109138a9` (M06 R01 remediation, 2026-09-27) Windows Studio wrote projects without
`working/authority.json` (only `.packlab-layout.json`, `working/project.json`, `working/state.json`). The current
`ProjectManager._read_authority` still reads that layout, and the first `commit_edit` writes the authority file.

## Fixture provenance

`tests/fixtures/studio/legacy_pre_authority_project_v1/` was produced by running the actual Studio sources from
`109138a9^` (extracted with `git show` to a scratch package): `new_project(...)` + one `commit_edit(...)`. Bytes are
unmodified; empty layout directories are recreated by the test. Synthetic content only.

## Tests (`tests/studio/test_project_migration.py`)

1. Legacy project opens through the public `open_project` boundary with correct identity/revision and no rewrite of
   source files; no authority file is created on open.
2. First edit migrates to the authority layout: schema `AUTHORITY_SCHEMA_VERSION`, original `project_id` and
   `created_at` preserved, revision 2, state as committed; reopen reads it. Two independent migrations with a pinned
   clock produce byte-identical `working/` files.
3. Future project schema, malformed `project.json`, non-object `state.json`, and future authority schema all raise
   `ProjectError` with `working/` bytes unchanged.

Result: 6 passed (plus existing `test_project.py`: 11 total). No production code change was required.

## Limits

Only one predecessor layout exists in history; `PROJECT_SCHEMA_VERSION` has always been `1.0`, so there is no
older declared schema number to migrate. Future schema bumps need their own migration and fixture.
