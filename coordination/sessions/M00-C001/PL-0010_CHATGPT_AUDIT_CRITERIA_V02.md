# PL-0010 — ChatGPT Strict Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0010_CODEX_PROMPT_V02.md

Artifact:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/RISK_REGISTER.md

Log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0010_CODEX_LOG_V02.md

All **32 criteria** are mandatory.

1. Root TASKS.md still identifies PL-0010 as the remediation frontier before material work.
2. Required Actor is CODEX.
3. Codex does not edit TASKS.md.
4. No M01 work is started.
5. Repository is synchronized safely before material work.
6. No unsafe Git operation is used.
7. No accepted sibling M00 artifact is modified.
8. RISK_REGISTER.md remains the only product/governance artifact modified.
9. Stable RISK IDs are preserved.
10. All required risk-register fields remain present.
11. Every Related PL task ID is validated against the actual text of current root TASKS.md.
12. No Related PL task ID is merely syntactically valid but semantically unrelated.
13. Capture-quality links point to capture-quality/guided-capture/reconstruction-validation work rather than Python/Ruff foundations.
14. Scale/calibration links point to calibration/measurement/physical-validation work.
15. iPhone/ARKit runtime links point to iOS capture/ARKit/device-validation work.
16. Host GPU/CUDA links point to diagnostics/capability/performance work.
17. Dependency links point to dependency/bootstrap/engine integration work.
18. Licensing links point to dependency/license/release-compliance work and do not misuse unrelated schema/mask tasks.
19. Apple signing/distribution links remain relevant to signing/distribution tasks.
20. Privacy/security links remain relevant to secrets/source-control/security audit tasks.
21. Schema/app compatibility links remain relevant to versioning/schema/migration tasks.
22. Supplier/private Kenya provenance links point to library/provenance/private-dataset/onboarding work rather than formatting tasks.
23. Reliability/reconstruction links point to subprocess/reconstruction/checkpoint/recovery/reliability work.
24. Risk descriptions, likelihood/impact, evidence/status, mitigations, contingencies and owner/actor remain coherent after link correction.
25. The full original PL-0010 risk coverage remains intact.
26. Current facts, hypotheses, planned mitigations and implemented controls remain clearly distinguished.
27. No physical accuracy, CUDA, legal certification, signing capability or production-readiness claim is invented.
28. git diff --check passes and git diff -- TASKS.md is empty for builder changes.
29. Exact changed-file/protected-file/privacy reviews pass.
30. V02 log records old -> new link mappings and why each new ID is actually related according to TASKS.md.
31. V02 log records validation/push evidence, does not self-assign PASS, and does not predeclare its future log commit SHA.
32. Actual GitHub diff/source/log are mutually consistent and no material PL-0010 defect remains.

## Closure

ChatGPT performs a full strict PL-0010 re-audit. If all 32 criteria pass, PL-0010 may close and M00 may receive a final milestone closure audit without reopening already accepted sibling children unless new evidence requires it.
