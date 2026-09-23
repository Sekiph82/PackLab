# PL-0078 — ChatGPT Strict Audit Criteria V01

Task: **PL-0078 — Add thermal/storage/battery warnings before and during long captures.**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CODEX_PROMPT_V01.md

All **20 criteria** are mandatory.

1. Root TASKS.md authorized M03-BATCH-001 / READY / CODEX before material work.
2. PL-0068 remains unchecked / OWNER_REQUIRED and this child does not fabricate or close that physical benchmark.
3. Repository synchronization is safe; no destructive reset/rebase/force-push/clean/stash of owner work is used.
4. Codex does not edit TASKS.md or ChatGPT audit artifacts.
5. Work stays inside M03 and does not start M04.
6. No secret, credential, provisioning private material, private Kenya scan/supplier asset or cache artifact enters public Git.
7. Changed files stay within the child scope plus justified minimal adjacent iOS/test/project files.
8. Existing iOS 17, Swift 6 strict concurrency, NextLevel 0.19.1, simulator fallback, diagnostics/privacy and PackScan contracts remain coherent.
9. The implementation materially satisfies the child mission: Add thermal/storage/battery warnings before and during long captures.
10. Requirement A is satisfied: Monitor ProcessInfo thermal state, available storage and battery state/level where available, with simulator-safe unavailable handling.
11. Requirement B is satisfied: Define deterministic warning/severity policy with conservative thresholds documented in code/tests; warnings must not masquerade as measured reconstruction quality.
12. Requirement C is satisfied: Evaluate conditions before capture starts and during an active session, updating the UI without blocking the main actor.
13. Requirement D is satisfied: Use fail-safe behavior for critically low storage or severe thermal conditions and make any hard-stop policy explicit.
14. Requirement E is satisfied: Add deterministic policy tests by injecting synthetic health snapshots rather than depending on the builder machine.
15. Positive, negative and immediate-boundary/state evidence is behavior-bearing rather than string-presence-only.
16. Existing accepted M01/M02 behavior relevant to the child remains unregressed.
17. Available tests/static/build validation are run truthfully; unavailable Xcode/device execution is reported rather than claimed.
18. `git diff --check` passes and builder `git diff -- TASKS.md` is empty.
19. The child Codex log exists, links prompt/criteria, records start/implementation/log commits, exact files, commands/results, limitations, privacy/signing review, remote visibility, and ends `READY_FOR_INDEPENDENT_AUDIT`.
20. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

Builder validation never self-closes this child. ChatGPT independently audits actual GitHub state after the milestone batch.
