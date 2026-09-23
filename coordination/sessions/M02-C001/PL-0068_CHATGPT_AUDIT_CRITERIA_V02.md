# PL-0068 — ChatGPT Strict Audit Criteria V02

Task: **PL-0068 — First physical calibration benchmark preparation / owner handoff**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0068_CODEX_PROMPT_V02.md

All **20 criteria** are mandatory for the builder handoff. Final PL-0068 completion additionally requires real owner-controlled physical benchmark evidence.

1. TASKS.md authorizes PL-0068 / READY / CODEX before material work.
2. Repository synchronization is safe and no destructive Git operation is used.
3. Codex does not edit TASKS.md or ChatGPT audit artifacts.
4. M03 and unrelated future work are not started.
5. No private Kenya scan, confidential supplier material, credential, signing material or cache artifact enters public Git.
6. Changed files stay within the authorized PL-0068 preparation scope plus only justified minimal adjacent files.
7. Existing PL-0060/61 mat geometry and verification contracts are reused rather than contradicted.
8. Existing PL-0065 iPhone 16 Standard main-camera binding/capture procedure is reused rather than contradicted.
9. A clear first-physical-benchmark procedure exists and separates nominal source geometry, owner-measured printed-mat geometry, captured evidence and benchmark result.
10. A benchmark record/template captures device, lens, resolution, orientation, zoom/focus, mat verification record, capture conditions, sample counts, accepted/rejected samples and provenance.
11. Benchmark outputs use millimetres and record known dimension, estimated dimension, signed/absolute error and percentage error with explicit formulas.
12. Rejected/invalid samples cannot be silently dropped from the record or aggregate statistics.
13. Acceptance thresholds, if any, are explicitly provisional/frozen and are not invented from unavailable physical results.
14. Any helper/parser/test added is deterministic and sensitivity-bearing against malformed or incomplete benchmark records.
15. No owner/native/physical measurements, device execution or benchmark result is fabricated.
16. If genuine owner-controlled physical evidence is unavailable, the builder stops with OWNER_REQUIRED and does not claim PL-0068 completion.
17. Relevant regression/lint checks pass; unavailable tools are reported truthfully.
18. git diff --check passes and git diff -- TASKS.md is empty.
19. PL-0068_CODEX_LOG_V02.md records exact files, commands/results, limitations, remote visibility and the owner handoff state.
20. Actual GitHub source/diff/docs/tests/log are mutually consistent and no material preparation defect remains.

## Final completion gate

PL-0068 itself may receive AUDITED_PASS only after real owner-controlled evidence exists for a printed verified PackLab mat and a physical benchmark session. Until then the correct project state is OWNER_REQUIRED, even if the preparation work passes audit.
