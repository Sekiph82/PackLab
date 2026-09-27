# M07-C001-R01 — ChatGPT Remediation Audit Criteria V04

Scope: evidence-boundary correction only for the PL-0160/PL-0161 R01 handoff.

Source audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CHATGPT_AUDIT_V03.md

V01 functional criteria and V02/V03 scope criteria remain inherited. All criteria below are mandatory.

1. Root TASKS.md authorizes M07-C001-R01 / CHANGES_REQUIRED / CODEX before material work.
2. V01, V02, and V03 prompts, criteria, logs, and audits remain immutable; no prior artifact is overwritten.
3. Implementation commit `508e4f2f63aa2e45c62d4e3de33b79297b7ac2b5`, the prior V02 head `c4f5eaa44c8c5635736011793e5704c4c4e65922`, and V03 head `736933cd44937a5e9afc82e18dffe63305105742` remain unchanged.
4. Accepted PL-0158, PL-0159, PL-0162 through PL-0165, all M06 authority, and the PL-0068 OWNER_REQUIRED gate remain unchanged.
5. No product code, tests, TASKS.md, ChatGPT audit/criteria artifact, dependency/lock file, generated artifact, binary, secret, private scan, or signing material changes in V04; only the new V04 Codex log is added by the Codex publication commit.
6. No PL-0166 or later task work starts.
7. The new log exists at the exact required path and uses full GitHub URLs for all material references.
8. The V04 log records actual staged `git diff --cached --check` output, expected/failure condition, and exit status; the staged check passes.
9. The V04 log records actual staged `git diff --cached --name-status` output showing only the new V04 log, with expected/failure condition and exit status.
10. The V04 log records the preserved implementation/V02/V03/start heads and clearly distinguishes pre-commit/staged evidence from the independent post-publication audit boundary.
11. The V04 log does not self-reference the future SHA of the commit containing its final content and does not claim pre-publication output as post-publication evidence.
12. The V04 log makes no new functional-test claim unless the test was actually rerun and ends exactly with `READY_FOR_INDEPENDENT_AUDIT`.
13. Codex does not edit TASKS.md, self-audit, assign AUDITED_PASS, or start PL-0166. ChatGPT independently verifies the final pushed head equals origin/main and the post-publication checkout is clean before closure.

Acceptance requires a fresh independent ChatGPT audit after the V04 log is pushed. This criteria file does not close PL-0160 or PL-0161.
