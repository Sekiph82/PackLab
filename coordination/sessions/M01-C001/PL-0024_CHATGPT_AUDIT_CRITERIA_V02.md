# PL-0024 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CODEX_PROMPT_V02.md
Prior audit evidence: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CHATGPT_AUDIT_V01.md

All **22 criteria** are mandatory.

1. Root TASKS.md authorized the M01 remediation batch / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. Root TASKS.md was not edited by Codex.
4. No M02 task or unrelated future product work was started.
5. No secret/private scan/confidential supplier/signing material/cache was committed.
6. Actual changed files are within the authorized remediation scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced audit is actually corrected, not merely documented.
8. Add safe cross-platform GPU adapter discovery, with a Windows path that can report non-NVIDIA adapters such as Intel Iris Xe is satisfied.
9. Keep generic GPU adapter discovery separate from CUDA evidence is satisfied.
10. Do not infer CUDA, dedicated VRAM, or compute capability from AdapterRAM, GPU name, generic memory fields, or mere adapter presence is satisfied.
11. Preserve safe timeouts, shell=False, no installation/system mutation, deterministic missing/error states, structured JSON and privacy omissions is satisfied.
12. Add injected/fake tests for a non-NVIDIA Windows adapter, NVIDIA adapter metadata without automatic CUDA proof, missing probes, and privacy/redaction is satisfied.
13. Original task behavior not implicated by the defect remains intact.
14. Relevant sibling M01 regressions remain intact.
15. Focused tests/static checks are meaningful and would fail on the pre-remediation defect.
16. git diff --check passes and builder TASKS.md diff is empty.
17. Protected-file/privacy/security review passes.
18. Platform-specific evidence is truthful and unavailable native/device evidence is not fabricated.
19. Remediation log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CODEX_LOG_V02.md and links prompt/criteria/audit evidence.
20. Log records start/implementation evidence, files changed, defect mapping, validations, failures/fixes, regressions, scope/privacy, limitations and push evidence.
21. Log does not self-assign AUDITED_PASS or predeclare its future log commit SHA and ends AWAITING_AUDIT.
22. Actual GitHub diff/source/log are mutually consistent and no material task defect remains.

## Closure

ChatGPT independently re-audits the full task against this remediation criteria plus the still-applicable original criteria. A PASS may close this task for M01 only if no new material regression is found.
