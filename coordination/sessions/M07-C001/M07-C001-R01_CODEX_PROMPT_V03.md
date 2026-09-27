# M07-C001-R01 — Codex Evidence-Contract Remediation Work Order V03

Tasks: PL-0160, PL-0161

Repository: https://github.com/Sekiph82/PackLab
Branch: main
Canonical tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Source audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CHATGPT_AUDIT_V02.md

V03 audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CHATGPT_AUDIT_CRITERIA_V03.md

This prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CODEX_PROMPT_V03.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CODEX_LOG_V03.md

## Authorization gate

Before material work, read TASKS.md. It must authorize M07-C001-R01 / CHANGES_REQUIRED / CODEX for PL-0160 and PL-0161. PL-0158, PL-0159, and PL-0162 through PL-0165 remain accepted. PL-0068 remains OWNER_REQUIRED. PL-0166 is not authorized.

Read the V02 audit, V02 criteria, V02 prompt, V02 log, coordination/CODEX_LOG_CONTRACT.md, and AL-PL-0007 before proceeding:

- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CHATGPT_AUDIT_V02.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CHATGPT_AUDIT_CRITERIA_V02.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CODEX_PROMPT_V02.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CODEX_LOG_V02.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/CODEX_LOG_CONTRACT.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_INDEX.md

## Bounded correction

V02 was product-neutral and diff-clean, but its log did not record actual validation/push results. Perform only this evidence-contract correction:

1. Do not edit or replace V01 or V02 artifacts.
2. Do not edit product code, tests, TASKS.md, any ChatGPT audit/criteria file, dependency/lock files, generated artifacts, binaries, secrets, private scans, or signing material.
3. Confirm starting origin/main is the current GitHub head containing this V03 work order, descends from prior V02 head c4f5eaa44c8c5635736011793e5704c4c4e65922, and has no unexpected product changes; stop and report any mismatch.
4. Create exactly the new V03 log at the required URL above.
5. The V03 log must record actual, not future-tense, results for every required validation:
   - the staged command git diff --cached --check and its exit status;
   - the staged command git diff --cached --name-status and the exact changed-file result, which must be only the new V03 log;
   - implementation SHA 508e4f2f63aa2e45c62d4e3de33b79297b7ac2b5 and prior V02 handoff head c4f5eaa44c8c5635736011793e5704c4c4e65922;
   - git push origin main success;
   - post-push freshness verification showing local main equals origin/main and a clean status;
   - full GitHub URLs for the prompt, criteria, log, tracker, implementation, and prior audit.
6. Do not place a SHA in the V03 log for the future commit that will contain that final log content. AL-PL-0007 and CODEX_LOG_CONTRACT.md require ChatGPT to record the final log-containing head in the audit after publication.
7. The V03 log must end exactly with READY_FOR_INDEPENDENT_AUDIT.

## Validation and publication

Stage only the new V03 log. Review the staged content before committing. Run the required staged checks and write their actual results into the V03 log before the final staging/commit. Then create one separate log-only commit, push origin/main, run a post-push fetch/ref/status freshness check, and ensure the final log already contains the recorded actual results. Do not make a follow-up edit commit to the V03 log after the publication commit.

Do not rerun or claim new functional tests unless actually rerun; V01 remains the independent functional/static evidence and V02 confirmed no product/test changes.

Stop after the handoff. Do not edit TASKS.md, self-audit, assign AUDITED_PASS, or start PL-0166.
