# CLAUDE_PEER_REVIEW — PL-0438 V02 (re-review of V01 fixes)

- Reviewer: Claude Code independent peer/security reviewer subagent (non-implementing). These are my own findings. This is not a CHATGPT_AUDIT or CODEX_PEER_REVIEW.
- Date: 2026-11-19. Base HEAD 4ee6bb09. The reviewed state is the uncommitted working tree.
- Constraints honoured: no source edits and no git writes. Mutants ran only on scratchpad copies.

## Reviewed file blobs (git hash-object)

Acceptance must be bound to a commit whose blobs equal these.

- tools/codex/task_queue.py 9011912e78771c89af5bcef4d4005c0d20ac875c
- tests/ci/test_codex_task_queue.py f0bd4b204abbd8b9f3dfe08cee4da3b44876665d
- scripts/codex/task-state.mjs 031c50488ccf47cf6d071257d63d2239dd31a7dd
- scripts/codex/task-state.test.mjs cb9aee1f6a1e21ee893b08f1d7c69baba40e5fc6
- scripts/codex/validate-task-state.mjs 4f53ab0f2b31056c53a32ce56e5bf22835074f65
- project-control/codex/AUTOMATION.md and AUTOMATION-PROMPT.md 5166665f246acf3fbc4da6533f9f642bb1aa6e22 (identical SUPERSEDED notice)
- Deleted:
  - scripts/codex/task-queue.mjs, dashboard-server.mjs, app-server-client.mjs, job-state.mjs;
  - their tests;
  - project-control/codex/owner-answers.jsonl.

## Verdict: PASS_WITH_NOTES

Recommended tracker status: CLAUDE_PEER_AUDITED_PASS, but only as a RESCOPED task: "read-only TASKS.md queue validators; Codex write-side autonomous queue retired and superseded". The original write-side scope was not delivered and must not be described as accepted.

## Evidence run

- .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/ci/test_codex_task_queue.py: 25 passed.
- node --test scripts/codex/*.test.mjs: 5 tests, 5 pass.
- tools/codex/task_queue.py --json on the real TASKS.md: exit 0, IDLE, 407/438.
- node scripts/codex/validate-task-state.mjs: exit 0, IDLE, 407/438.
- git diff --check on the scope: clean.
- git grep for the deleted file names outside coordination/sessions: no hits. Only historical session logs mention them.

## V01 findings disposition

- P1-1: RESOLVED in-repo.
  - The writer, dashboard, inbox, App Server client and job-state are deleted. No process spawn remains, and nothing left can write TASKS.md: both remaining modules only read.
  - AUTOMATION*.md now carry the SUPERSEDED notice.
  - Remaining owner action, outside the repo: disable the external Codex automation packlab-autonomous-task-queue. It is still NOT_VERIFIED. Any Codex agent could edit TASKS.md directly regardless of these validators, so this is a governance item, not a code defect.
- P2-1, P2-2, P2-3, P2-4: MOOT. The code is removed and no references remain.
- P2-5: RESOLVED for Python, which is the CI-enforced validator. Re-run mutants:
  - Python, 16 of 18 killed: idle widened or case-insensitive; idle task-ID check; actor loosened; title; branch; netloc/port; scheme; exact Execution Rules match; indentation guard; malformed guard; idle in-progress; marker; duplicate IDs; multiple in-progress.
  - Python survivors:
    - removing the CODEX first-token check (task_queue.py:88). No Python test uses a CLAUDE_CODEX_* actor; the Node test does.
    - removing the username-is-None check (line 118). This is equivalent, because the netloc == github.com check on line 120 already rejects userinfo.
  - Node, 13 of 16 killed.
  - Node survivors, all with no Node test: removing the status-marker mismatch check (task-state.mjs:67), the multiple-in-progress check (line 69) and the duplicate-ID check (line 36).
- P2-6: RESOLVED.
  - Node checks repository Sekiph82/PackLab and branch main exactly (lines 55-57).
  - Both parsers stop at a heading that starts with "# Execution Rules".
  - Both reject non-canonical checkbox items that carry an ID, whether indented, using [X], or using a star bullet.
  - Python requires netloc == github.com, which excludes ports and userinfo.
- P2-7: RESOLVED. The live-TASKS.md test was removed from both suites, so CI no longer depends on tracker prose.
- P3 idle/actor regexes: RESOLVED. The idle regex is case-sensitive, and a task ID inside an idle line is rejected. The actor must be CLAUDE or CLAUDE_[A-Z0-9_]+ followed by whitespace or end of string, and a first token containing CODEX is rejected. All of this is verified by tests.
- P3 CRLF rewrite, junction parent directories, inbox hygiene: MOOT (code removed).
- P3 job.json shadow ledger: declared historical and non-status in AUTOMATION.md. Acceptable. The PL-0438 job.json still says COMPLETED_LOCAL / AUTONOMOUS_QUEUE_ARMED. That is historical Codex evidence and must not be cited as status.

## Remaining notes (P3, non-blocking)

1. Add a Python actor case CLAUDE_CODEX_RUNNER (kills the surviving mutant at task_queue.py:88).
2. Add Node negative tests for the marker mismatch, more than one in-progress row, and duplicate IDs. Node tests are not run in any GitHub workflow, so Python is the only CI-enforced validator. Either run node --test scripts/codex/*.test.mjs locally per task, or treat the Node validator as advisory.
3. Python and Node still differ:
   - Python accepts the exact https://github.com/Sekiph82/PackLab(.git) URL and dotted or non-PL IDs; Node accepts only the short repository form and PL-#### IDs;
   - Node accepts status COMPLETE; Python does not;
   - Python does not require milestone or sprint fields.
   All of these fail closed or are harmless for the real tracker, but should be documented if both stay.
4. The malformed-row guard is a broad heuristic. Any list item in the ledger that starts with "[" and contains an ID now raises, e.g. a markdown link bullet such as "- [notes](x) PL-0123". This is a fail-closed false-positive risk for future tracker edits.
5. The Python parser uses str.splitlines(), which also splits on U+2028/VT/FF. With the writer gone, nothing in-repo injects these. Python is still a theoretical parser differential versus Node and GitHub rendering.
6. The owner first name is still a regex literal at task-state.mjs:95. Minor.

## PL-0438 original criteria (read-only scope)

- Read-only validator: MET (no writes remain in either language).
- Explicit fields, no checkbox inference: MET (IDLE never infers a task).
- Dotted IDs plus exact ID/title identity: MET (Python), with a tested title mismatch.
- Rejects malformed/duplicate rows, status mismatch, multiple in-progress rows, foreign repo/branch: MET (Python fully tested; Node gaps per note 2).
- JSON output and nonzero exit: MET (--json; --task PL-0438 exits 2 on the idle tracker by design).
- TASKS.md is the only tracker: MET after the inbox and writer were removed and job.json was declared non-status.
- Delegation, zero-CI and PL-0354 clauses: SUPERSEDED by the 2026-11-10 Claude handoff. Not acceptance criteria any more.
- Heartbeat automation: RETIRED by policy. Disabling it externally is owner-only and NOT_VERIFIED. It should be recorded as an open owner action, not as accepted work.

## Closure recommendation

PL-0438 can be closed [x] as CLAUDE_PEER_AUDITED_PASS only with the rescope recorded in the TASKS.md row:
- what was accepted: the read-only TASKS.md validators;
- what was retired as superseded: the write-side autonomous queue, dashboard and owner-answer inbox;
- owner action: disable the external Codex heartbeat automation;
- the commit SHA, whose blobs must match the hashes above.

If the coordinator prefers not to accept a rescoped deliverable for a task added outside the 437-task plan, the equally valid alternative is to close it as SUPERSEDED/WITHDRAWN and keep the validators as tooling. Notes 1 and 2 are cheap and should land before or with the closing commit, but they do not block.
