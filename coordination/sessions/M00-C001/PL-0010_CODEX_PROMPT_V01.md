# PL-0010 - Codex Child Work Order V01
Task: **PL-0010 - Create project risk register with technical, licensing, capture-quality, signing and hardware risks**

Repository: https://github.com/Sekiph82/PackLab
Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CODEX_PROMPT_V01.md
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0010_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0010_CHATGPT_AUDIT_CRITERIA_V01.md
Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0010_CODEX_LOG_V01.md

Read https://github.com/Sekiph82/PackLab/blob/main/TASKS.md, https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md, https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md and https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_POLICY.md. TASKS.md must still authorize M00-BATCH-001 / CODEX. Never edit TASKS.md.

## Objective
Create https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/RISK_REGISTER.md.

## Mandatory content
1. Use stable risk IDs and fields for category, description, likelihood, impact, evidence/status, mitigation, contingency, owner/actor and related PL task IDs.
2. Cover glossy/transparent/low-texture photogrammetry risk.
3. Cover metric-scale/calibration error and distinguish visual similarity from physical dimensional evidence.
4. Cover iPhone 16 Standard no-LiDAR and ARKit/runtime variability.
5. Cover host GPU/CUDA/performance uncertainty without treating integrated AdapterRAM as dedicated VRAM.
6. Cover COLMAP/OpenMVS/Open3D/OpenCascade/Blender/PySide6 dependency, packaging and license risks.
7. Cover OpenMVS AGPL and other license obligations without giving legal certification.
8. Cover Apple signing/provisioning/free-first distribution uncertainty.
9. Cover public-repository secret/private-data leakage.
10. Cover schema/app compatibility and migration risk.
11. Cover supplier/private Kenya asset provenance and availability.
12. Cover disk/storage/long-running reconstruction failure and reproducibility.
13. Distinguish current evidence from hypotheses and do not claim future mitigations already exist.

## Validation and scope
Run and record `git diff --check`, `git diff -- TASKS.md`, `git status --short --branch`, explicit checks for every requirement, exact changed-file review, protected-file review and privacy/security review.
Review the new file with `git add -N docs/architecture/RISK_REGISTER.md` plus `git diff -- docs/architecture/RISK_REGISTER.md`, or equivalent staged review.
Do not start the next child until this child is validation-green and its log is pushed. Do not start M01. Stop the whole batch on blocker, authorization mismatch, unsafe divergence, privacy risk or ADR_REQUIRED.

## Log
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0010_CODEX_LOG_V01.md. Record full prompt/criteria URLs, child start, implementation/evidence commit, files read/changed, validations with expected/failure/actual results, failures/fixes, scope/privacy checks, push evidence and limitations. End `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit or predeclare the future log commit SHA.
