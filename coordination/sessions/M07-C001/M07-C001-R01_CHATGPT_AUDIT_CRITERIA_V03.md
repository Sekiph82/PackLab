# M07-C001-R01 — ChatGPT Remediation Audit Criteria V03

Scope: evidence-contract correction only for the PL-0160/PL-0161 R01 handoff.

Source audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CHATGPT_AUDIT_V02.md

V01 functional criteria and V02 scope criteria remain inherited. All criteria below are mandatory.

1. Root TASKS.md authorizes M07-C001-R01 / CHANGES_REQUIRED / CODEX before material work.
2. V01 and V02 prompts, criteria, logs, and audits remain immutable; no prior artifact is overwritten.
3. Implementation commit 508e4f2f63aa2e45c62d4e3de33b79297b7ac2b5 and the audited implementation/test files remain unchanged.
4. Accepted PL-0158, PL-0159, PL-0162 through PL-0165, all M06 authority, and the PL-0068 OWNER_REQUIRED gate remain unchanged.
5. No product code, tests, TASKS.md, ChatGPT audit/criteria artifact, dependency/lock file, generated artifact, binary, secret, private scan, or signing material changes in V03; only the new V03 Codex log is added.
6. No PL-0166 or later task work starts.
7. The new log exists at the exact required path and uses full GitHub URLs for all material references.
8. The V03 log records the actual staged git diff --cached --check command, expected/failure condition, actual result, and exit status; the staged check passes.
9. The V03 log records the actual staged git diff --cached --name-status result showing only the new V03 log.
10. The V03 log records implementation SHA 508e4f2 and prior V02 head c4f5eaa, successful git push origin main, and post-push local-main/origin-main equality with clean status.
11. The V03 log does not self-reference the future SHA of the commit containing its final content; the independent audit records that final pushed head.
12. The V03 log ends exactly with READY_FOR_INDEPENDENT_AUDIT and makes no new functional-test claim unless the test was actually rerun.
13. Codex does not edit TASKS.md, self-audit, assign AUDITED_PASS, or start PL-0166; closure remains gated on a fresh independent ChatGPT audit.

Acceptance requires a fresh independent ChatGPT audit after the V03 log is pushed. This criteria file does not close PL-0160 or PL-0161.
