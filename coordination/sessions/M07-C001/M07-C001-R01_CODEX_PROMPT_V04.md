# M07-C001-R01 — Codex Evidence-Contract Remediation Work Order V04

Tasks: PL-0160, PL-0161

Repository: https://github.com/Sekiph82/PackLab
Branch: main
Canonical tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Source audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CHATGPT_AUDIT_V03.md

V04 audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CHATGPT_AUDIT_CRITERIA_V04.md

This prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CODEX_PROMPT_V04.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CODEX_LOG_V04.md

## Authorization gate

Before material work, read TASKS.md. It must authorize M07-C001-R01 / CHANGES_REQUIRED / CODEX for PL-0160 and PL-0161. PL-0158, PL-0159, and PL-0162 through PL-0165 remain accepted. PL-0068 remains OWNER_REQUIRED. PL-0166 is not authorized.

Read the V03 audit, V03 criteria, V03 prompt, V03 log, coordination/CODEX_LOG_CONTRACT.md, and coordination/AUDIT_INDEX.md before proceeding.

## Bounded correction

V03 was product-neutral and its commit changed only the new V03 log, but its push/freshness evidence was explicitly pre-publication at `aa9dac5e97a9dd3af994e87b6b7dc23cb0552844` rather than evidence for the final log-containing commit `736933cd44937a5e9afc82e18dffe63305105742`. Perform only this evidence-boundary correction:

1. Do not edit or replace V01, V02, or V03 artifacts.
2. Do not edit product code, tests, TASKS.md, any ChatGPT audit/criteria file, dependency/lock files, generated artifacts, binaries, secrets, private scans, or signing material.
3. Confirm starting `origin/main` is the current GitHub head containing this V04 work order, descends from V03 head `736933cd44937a5e9afc82e18dffe63305105742`, and has no unexpected product changes; stop and report any mismatch.
4. Create exactly the new V04 log at the required URL above.
5. The V04 log must record actual results for the staged validation of its final content:
   - `git diff --cached --check`, including the actual output and exit status;
   - `git diff --cached --name-status`, showing exactly the new V04 log and including the actual output and exit status;
   - preserved implementation SHA `508e4f2f63aa2e45c62d4e3de33b79297b7ac2b5`, V02 handoff head `c4f5eaa44c8c5635736011793e5704c4c4e65922`, V03 final head `736933cd44937a5e9afc82e18dffe63305105742`, and the V04 starting head;
   - full GitHub URLs for the prompt, criteria, log, tracker, implementation, V03 audit, and V03 head.
6. The log must explicitly distinguish pre-commit/staged evidence from post-publication audit evidence. Do not label a pre-publication command as post-publication, and do not self-record the future SHA of the commit containing the final log. ChatGPT will independently verify the final pushed head and remote freshness after publication.
7. Do not rerun or claim functional/static tests unless actually rerun; the unchanged implementation remains bounded by the prior independent V01 audit.
8. The V04 log must end exactly with `READY_FOR_INDEPENDENT_AUDIT`.

## Validation and publication

Stage only the new V04 log. Review the staged content and run the required staged checks against the final staged content. Create one separate log-only commit and push `origin main`. After the commit, run a post-publication fetch/ref/status freshness check. Do not make a follow-up edit commit to the V04 log. The post-publication command results are for the independent ChatGPT audit; the V04 log must not fabricate or self-reference its future containing SHA.

Stop after the handoff. Do not edit TASKS.md, self-audit, assign AUDITED_PASS, or start PL-0166.
