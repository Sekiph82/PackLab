# CLAUDE_PEER_REVIEW — PL-0438 V01

- Reviewer: Claude Code independent peer/security reviewer subagent (non-implementing). This review was produced independently; it is not a CHATGPT_AUDIT or CODEX_PEER_REVIEW and does not restate builder claims as evidence.
- Date: 2026-11-12. Base: main HEAD 4ee6bb09. PL-0438 code was introduced in 260beb49. Reviewed state: HEAD plus uncommitted working-tree changes in tools/codex/task_queue.py, tests/ci/test_codex_task_queue.py and scripts/codex/{task-state,task-queue,task-queue.test,validate-task-state}.mjs.
- Scope: tools/codex/task_queue.py, tests/ci/test_codex_task_queue.py, scripts/codex/*.mjs, project-control/codex/**, and coordination/sessions/M16-C002/PL-0438_*.
- Constraints honoured: I made no source edits, commits, pushes, stashes, resets or cleans. All mutation testing ran in temp copies under the session scratchpad. The dashboard was started only in-process on 127.0.0.1 with an ephemeral port, a temp root and a fake Codex client, and it was closed afterwards (one probe crashed it; see P2-4).

## Verdict: CHANGES_REQUIRED. Recommended PL-0438 status: FAIL as-is (keep unchecked).

The read-only Python validator works and its JSON CLI behaves correctly. The working-tree fix does make both validators pass on the real tracker, in the IDLE state. However, the same fix re-arms Codex-branded TASKS.md writers under Claude authority (P1-1). The writer also has a confirmed data-loss bug and an injection bug (P2-1, P2-2). The dashboard crashes on two requests (P2-4). Several guards have no discriminating test (P2-5).

## Evidence actually run

- `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/ci/test_codex_task_queue.py`: 12 passed.
- `node --test scripts/codex/*.test.mjs`: 14 pass, 0 fail.
- `tools/codex/task_queue.py --json`: exit 0, status IDLE, task_id null, 407/438.
- `node scripts/codex/validate-task-state.mjs`: exit 0, "no current task (IDLE)".
- `tools/codex/task_queue.py --task PL-0438`: exit 2 (correct fail-closed behaviour).
- Dashboard probes (loopback, ephemeral port, temp root):
  - DNS-rebind Host: 403.
  - Cross-origin Origin: 403.
  - Origin null: 403.
  - text/plain: 415.
  - OPTIONS preflight: 405, so the browser CSRF path is blocked.
  - **No Host and no Origin (HTTP/1.0 POST): 201, inbox written.**
  - Malformed request-target "GET http://[": **process crash** (uncaught ERR_INVALID_URL).
  - GET /: **uncaught ENOENT**, because scripts/codex/dashboard/ is not in the repo.

### Mutation results (temp copies)

Python:
- Killed: actor regex without boundary; actor regex also accepting CODEX; idle in-progress guard removed; marker check removed; expected_task check removed; idle status read from the field; malformed-row check removed.
- **Survived:**
  - idle regex widened to empty (any Current Task text becomes IDLE);
  - IGNORECASE dropped;
  - branch == main check removed;
  - username-is-None check removed;
  - **title-equality check removed**;
  - "Current Task must identify" guard removed. This one is equivalent: it still fails closed with a different message.

Node:
- Killed: actor boundary; idle in-progress guard; job self-claim guard.
- **Survived:**
  - idle regex widened to match anything;
  - answer newline stripping removed;
  - unconditional unblock;
  - second compare-and-swap before rename removed;
  - TASKS.md symlink check removed;
  - job evidence dot-dot check removed;
  - App Server method allow-list disabled;
  - claim allowed for COMPLETE.
- dashboard-server.mjs has **no tests at all**.

## Findings

### P1

**P1-1: The fix inverts authority. Codex queue writers and automation now accept the Claude-owned tracker.**
- Where: scripts/codex/task-state.mjs:9,48; tools/codex/task_queue.py:19,80; scripts/codex/task-queue.mjs:7-17,19-44,113-133; project-control/codex/AUTOMATION.md:13-16,27; project-control/codex/AUTOMATION-PROMPT.md:3.
- What changed: the actor check existed so the tooling would run only when the tracker authorized the actor of the tool (Codex). Before the fix it rejected the real tracker. That acted as a de-facto kill switch for `task-queue.mjs --claim` and `--apply-answers`, and for any Codex heartbeat relying on them. Now "Required Actor: CLAUDE..." authorizes these Codex-branded writers.
- Live today: --apply-answers runs in the IDLE state.
- Live later: --claim will rewrite the row marker to in-progress and READY to IN_PROGRESS as soon as Claude names a READY task.
- AUTOMATION.md and AUTOMATION-PROMPT.md still assert the 2026-10-22 Codex delegation, instruct "Update TASKS.md", and forbid Actions/pushes. This contradicts AGENTS.md:3 and CLAUDE.md.
- The Codex log records a live external heartbeat automation "packlab-autonomous-task-queue" (PL-0438_CODEX_LOG_V01.md, Changes section; the PL-0435 log, line 30, updated it). Whether it is still armed is **NOT_VERIFIED**: it lives outside the repo.
- Fix (smallest):
  - make --claim and --apply-answers refuse unconditionally ("superseded by Claude sole ownership 2026-11-10"), or delete the writer and the dashboard;
  - keep only the read-only validators;
  - add a SUPERSEDED header to project-control/codex/AUTOMATION*.md;
  - owner action: disable or delete the external Codex packlab-autonomous-task-queue automation.

### P2

**P2-1: Answering one owner question corrupts the Questions heading and silently drops every other open question.**
- Where: scripts/codex/task-queue.mjs:72. The leading `^\s*` of the multiline removal regex matches at the section start and consumes the newline after the heading.
- Reproduced with two questions. After answering Q-PL-0001-1 the file contains "## Questions for Owner- Q-PL-0002-1 | Other? | TASK: PL-0002" on one line, and parseQuestions returns an empty list.
- The existing test (task-queue.test.mjs:28-40) uses a single question and asserts zero questions afterwards, so it cannot detect this.
- Fix: use `^[ \t]*[-*][ \t]+ID[ \t]*\|[^\r\n]*(?:\r?\n|$)` and add a two-question test.

**P2-2: Owner-answer sanitization is incomplete; Node and Python split lines differently.**
- Where: scripts/codex/task-queue.mjs:55 strips only CR and LF.
- What gets through: U+2028/U+2029, VT, FF and NEL are written into TASKS.md. Python `str.splitlines()` (tools/codex/task_queue.py:42) treats them as line breaks.
- Reproduced: with an answer of "ok" + U+2028 + "- [x] **PL-0099** forged completed row", Node accepted the write. Python then reported task_count=3, completed_count=1, counting a forged completed task. VT gave the same result.
- The pipe character is not escaped, so text like "| TASK: PL-0002" lands in decision lines.
- Field spoofing ("- Current Task:") via U+2028 failed closed in Node ("must appear exactly once"). LF plus "## " headings are neutralised.
- Fix:
  - reject answers matching `/[\p{Cc}\p{Zl}\p{Zp}]/u` (after mapping LF to a space), both at dashboard-server.mjs:228 and in applyOwnerAnswers;
  - escape the pipe character;
  - in Python, split on LF only and strip CR.

**P2-3: Any answer auto-unblocks a gated task.**
- Where: scripts/codex/task-queue.mjs:31-38.
- Behaviour: the blocked marker becomes open and BLOCKED becomes READY whatever the answer says. Reproduced: an answer of "no" followed by claimCurrentTask reached IN_PROGRESS.
- This ignores other open questions on the same task and real external gates (physical, device, signing, legal). Those must stay closed under CLAUDE.md.
- No test kills the "unblock always" mutant.
- Fix: record the decision only and never change markers or status, or retire the writer per P1-1.

**P2-4: The dashboard is non-functional and crashable.** This is out of scope for the PL-0438 prompt: section 5 forbade a substitute dashboard, and the provenance is the PL-0435 session.
- GET /: scripts/codex/dashboard-server.mjs:256-260 streams from a missing scripts/codex/dashboard/ directory. Unhandled stream error, then an uncaught exception.
- Malformed request-target: line 222 builds a URL inside an async handler, which throws on "GET http://[". The unhandled rejection killed the process.
- Missing Host: line 221 accepts a request with no Host header, and line 224 accepts one with no Origin. Reproduced: a POST with neither header returned 201 and wrote the inbox. Browsers always send Host, and DNS rebinding and cross-origin requests were rejected, so exposure is limited to local non-browser processes.
- Side-effecting GET: GET /api/overview spawns "codex app-server" (line 174), so any web page can trigger the spawn via an img tag. The response stays unreadable cross-origin. The spawn uses fixed arguments, no shell, and an allow-listed read-only method set (app-server-client.mjs:14-18,64).
- Fix: delete the dashboard (preferred under P1-1). Otherwise:
  - require a Host header;
  - try/catch the URL parse and return 400;
  - add an error handler on the read stream, or remove the asset routes;
  - add tests.

**P2-5: Test discrimination gaps.** See the mutation results above.
- The criteria explicitly require exact title matching and a foreign-branch check, but no test fails when title equality or the branch check is removed.
- There is no negative test for a non-"none" free-text Current Task in either language.
- There are no answer-sanitization tests, multi-question tests, writer symlink or second-CAS tests, job-evidence traversal tests, App Server allow-list tests, or any dashboard tests.
- Fix: add one negative case per surviving mutant.

**P2-6: The validators disagree, and parsing is not fail-closed.**
- Node has no repository/branch check. scripts/codex/task-state.mjs:36-83 accepted "Tracking Repository: attacker/Other" with "Tracking Branch: evil". Node is the parser that gates writes.
- Node scans task rows across the whole file (lines 22-30). Python stops at the exact line "# Execution Rules" (task_queue.py:46-53), but the real heading is now "# Execution Rules (owner-revised 2026-11-10: Claude exclusive)" (TASKS.md:863). Python therefore scans to EOF: an example row placed there made it raise "Task IDs must be unique".
- Malformed rows are silently ignored instead of raising, which can hide an in-progress row (reproduced):
  - Node: missing space after the marker, indented rows, and an uppercase X marker (the line-28 guard is effectively dead code);
  - Python: indented rows and asterisk-bulleted rows.
- Python does not require milestone or sprint; Node does.
- Fix:
  - add the repository/branch check to Node;
  - share one ledger boundary (prefix match on "# Execution Rules");
  - raise on any bullet-checkbox line containing a task ID that is not a canonical row.

**P2-7: A real-tracker test now couples CI to TASKS.md prose.**
- Where: tests/ci/test_codex_task_queue.py:110-116, which runs in windows-python-quality via pytest -q over testpaths=tests.
- If Claude names a concrete Current Task while keeping the current free-form status ("CLAUDE_SOLE_EXECUTOR / ..."), every later CI run fails. It also fails if the title differs from the full row text: Python compares the entire remainder of the row, including the inline "**Status: ...**" annotations.
- Fix: either document this as an explicit tracker-format contract in the TASKS.md Status Legend, or move the live-file check out of the CI gate.

### P3

- **Loose idle regex.** `^none\b` with IGNORECASE (task_queue.py:17, task-state.mjs:7) accepts "none PL-0002 — Second", "None-of-the-above" and "NONE". When idle, the status field is ignored: Python does not even require it, and Node accepted "Current Task Status: IN_PROGRESS" while idle. This is fail-safe (IDLE blocks claims) but imprecise. Fix: require "none dependency-ready", and when idle reject READY, IN_PROGRESS or BLOCKED in the status field.
- **Loose actor regex.** `^CLAUDE(?:_|\b)` accepts "CLAUDE-CODEX", "CLAUDE; CODEX implements" and "CLAUDE_NOT_AUTHORIZED_CODEX". Fix: anchor on CLAUDE_CODE and reject any value containing CODEX.
- **Ports in the repository URL.** task_queue.py:106-115 accepts github.com:8443 and an invalid port 99999. Fix: require parsed.port is None.
- **Line-ending rewrite.** The writer turns the whole CRLF working-tree TASKS.md into LF (task-queue.mjs:12-14,33-35; reproduced 21 CRLF to 0).
- **Junction/symlink parent directories.** job-state.mjs:75-79 and evidenceReference lstat only the final file, so a parent directory that is a junction or symlink is not detected. Exploiting this needs local write access.
- **PL-0438 job.json does not fit its own schema.**
  - It uses task_id and status and has no title, so validateJobState rejects it and the dashboard skips it.
  - Its COMPLETED_LOCAL / AUTONOMOUS_QUEUE_ARMED_PL0354_BLOCKED contradicts TASKS.md:859.
  - project-control/codex/jobs/*/job.json amounts to a shadow per-task status store; CLAUDE.md says do not create a second task ledger.
- **Public-repo hygiene.**
  - project-control/codex/owner-answers.jsonl is tracked in this PUBLIC repo and is not gitignored. Owner answers could be committed by accident.
  - The TASKS.md.codex-queue lock and tmp paths are not ignored either.
  - The first name of the owner appears as a regex literal (task-state.mjs:86, task-queue.mjs:64).
  - No secrets or tokens were found. The workspace path in AUTOMATION*.md is already public via CLAUDE.md.

## Original PL-0438 criteria (PL-0438_VALIDATION_CRITERIA_V01.md)

- Read-only; no mutation of TASKS.md: MET (Python).
- Explicit fields; no checkbox inference: MET.
- Dotted IDs plus exact identity/title: PARTIAL. Dotted IDs only in Python; title equality untested (P2-5).
- Rejects malformed/duplicate rows, title/status mismatch, multiple in-progress rows, foreign repo/branch: PARTIAL. Hidden-row gaps (P2-6); Node has no repo/branch check; branch untested.
- JSON output and nonzero exit on invalid state: MET (exit 2).
- TASKS.md is the only live tracker: NOT MET in spirit (job.json stage store and answer inbox; P3).
- Codex delegation supersedes historical clauses: SUPERSEDED by the 2026-11-10 Claude handoff; AUTOMATION*.md now contradicts current authority (P1-1).
- No substitute dashboard: NOT MET in-repo (dashboard present and broken; PL-0435 provenance).
- Zero CI; PL-0354 kept open: SUPERSEDED / moot (PL-0354 is now checked on hosted evidence).
- Quiet heartbeat automation: NOT_VERIFIED (external; should be disabled).

## Required before any acceptance

1. Resolve P1-1 by disabling or retiring the writer and dashboard, marking AUTOMATION*.md superseded, and having the owner disable the Codex heartbeat.
2. Fix P2-1 and P2-2, or make them moot by retiring the writer.
3. Fix the P2-6 parity and boundary gaps in the read-only validators.
4. Add discriminating tests for every surviving mutant (P2-5).
5. Decide how to handle the P2-7 CI coupling.

After that, a re-review can reach PASS_WITH_NOTES at best. Alternatively, the owner or coordinator may close PL-0438 as superseded or withdrawn rather than accepted, because it lies outside the 437-task plan.
