# PL-0067 — ChatGPT Strict Audit Criteria V02

Task: **PL-0067 — Synthetic calibration ground-truth reconciliation**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0067_CODEX_PROMPT_V02.md

All **20 criteria** are mandatory.

1. TASKS.md authorizes PL-0067 / READY / CODEX before material work.
2. Repository synchronization is safe and no destructive Git operation is used.
3. Codex does not edit TASKS.md or any ChatGPT audit artifact.
4. PL-0068 and M03 are not started.
5. No private Kenya scan, confidential supplier material, credential, signing material or cache artifact enters public Git.
6. Changed files stay within the authorized PL-0067 scope plus only justified minimal adjacent files.
7. Deterministic synthetic calibration cases use explicit known marker geometry, dimensions, units, coordinate conventions and reproducible generator parameters.
8. Synthetic evidence exercises the actual marker-detection contract, not only hand-constructed post-detection MarkerObservation objects.
9. Synthetic evidence exercises scale estimation, confidence scoring and calibration-profile compatibility/reuse logic without private images.
10. Ideal, noisy, partial, degenerate and inconsistent cases have explicit expected outcomes/error bounds.
11. Sensitivity-bearing tests fail when scale math, real-world units, corner ordering or marker geometry are materially perturbed.
12. The post-remediation PL-0063 geometry rejection and PL-0064 hard residual/spread gates remain enforced.
13. The post-remediation PL-0066 provenance contract remains fail-closed: synthetic/public evidence must not masquerade as owner/native/physical calibration evidence or become reusable merely to make a test pass.
14. Positive, negative and immediate boundary evidence is meaningful and would detect a broken implementation rather than only string/document presence.
15. Existing accepted PackScan/calibration contracts remain unregressed.
16. Ruff and relevant pytest pass; mypy is run when available and any unavailable tool is reported truthfully.
17. git diff --check passes and git diff -- TASKS.md is empty.
18. Platform/device/physical evidence boundaries are truthful; no native/device/physical result is fabricated.
19. PL-0067_CODEX_LOG_V02.md exists, links this prompt/criteria, records exact implementation/evidence, commands/results, limitations and remote visibility, and ends READY_FOR_INDEPENDENT_AUDIT.
20. Actual GitHub source/diff/tests/log are mutually consistent and no material PL-0067 defect remains.

## Closure

Builder validation never self-closes the task. ChatGPT independently audits the actual GitHub V02 state before PL-0067 can be checked complete or PL-0068 can be considered.
