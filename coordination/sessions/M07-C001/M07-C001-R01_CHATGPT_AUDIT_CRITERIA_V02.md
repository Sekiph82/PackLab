# M07-C001-R01 — ChatGPT Remediation Audit Criteria V02

Scope: **evidence-only correction for PL-0160 and PL-0161 R01 handoff**

Source audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CHATGPT_AUDIT_V01.md

V01 criteria remain inherited for all functional, architectural, regression, security and scope requirements. The V02 audit must independently confirm the V01 implementation remains unchanged and that the following correction closes the only V01 finding.

All criteria below are mandatory.

1. Root `TASKS.md` authorizes M07-C001-R01 / CHANGES_REQUIRED / CODEX before material work.
2. The V01 audit remains immutable and records only the trailing-whitespace finding; no V01 artifact is overwritten.
3. Implementation commit `508e4f2f63aa2e45c62d4e3de33b79297b7ac2b5` remains the unchanged PL-0160/PL-0161 implementation evidence commit.
4. Accepted PL-0158, PL-0159, PL-0162 through PL-0165, all M06 authorities, and PL-0068 OWNER_REQUIRED remain unchanged.
5. No product code, tests, TASKS.md, ChatGPT audit/criteria artifact, dependency/lock file, generated artifact, binary, secret, private scan, or signing material is changed by V02; only the new V02 Codex log may be added.
6. No PL-0166 or later task is started.
7. The new log exists at the exact required path:
   https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CODEX_LOG_V02.md
8. The V02 log records the exact implementation SHA and the V02 log-only commit SHA, uses full GitHub URLs, and ends exactly with `READY_FOR_INDEPENDENT_AUDIT`.
9. The V02 log contains no trailing whitespace, and the final published V02 handoff diff passes `git diff --check` with exit code 0.
10. The V02 log does not claim unrerun functional checks as newly rerun; it accurately identifies the V01 independent audit as the evidence for unchanged functional behavior.
11. The inherited V01 criteria 1–23 and 25–28 remain satisfied by the unchanged implementation and evidence; the V01 audit's functional findings are not silently broadened or weakened.
12. Closure remains gated on a fresh independent ChatGPT audit; Codex does not edit TASKS.md, self-audit, assign `AUDITED_PASS`, or start PL-0166.

Acceptance requires a fresh independent ChatGPT audit after the V02 log is pushed. This criteria file does not itself close PL-0160 or PL-0161.
