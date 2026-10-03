# M12-C001 - Remediation & Continuation ChatGPT Audit Criteria V02

Scope: **shared cancellation determinism remediation, PL-0269 V02 closure, then PL-0270 through PL-0288 continuation**

All criteria are mandatory.

1. **Frontier integrity:** execution starts from `8ec5b4c822d4b97d13eea125c64691971baf3b58` or a verified descendant preserving PL-0268/PL-0269 evidence. PL-0268 is not reimplemented and PL-0270+ was not pre-started.
2. **Root-cause remediation:** pre-set `cancel_event` is handled deterministically before child execution can outrun cancellation. The fix belongs in the shared runner contract, not PL-0269 geometry code.
3. **No test laundering:** the solution does not weaken/remove/skip/xfail the cancellation assertion and does not use arbitrary sleeps or retry-until-green behavior.
4. **No-spawn proof:** a direct regression demonstrates that a pre-set cancellation event prevents child-side effects/process execution and yields structured `cancelled=True` evidence.
5. **Behavior preservation:** live cancellation still terminates runner-owned process trees; timeout remains distinct; success/nonzero process semantics remain intact.
6. **Repeatability proof:** the existing `test_stage_cancellation_is_distinct` passes at least 20 sequential invocations at the remediation revision.
7. **Global gate:** the exact locked full suite passes **twice consecutively** at the same final remediation revision before PL-0269 is closed.
8. **PL-0269 implementation reuse:** `c6f935fc0308256af528cc596ff01e55d3242763` remains the PL-0269 implementation unless direct child-scope evidence justifies a separately documented change.
9. **PL-0269 child gates:** dedicated handle-void/predecessor tests and changed-file static/scope/security checks pass after remediation; source authority remains candidate-only/non-destructive and hidden 3D extent remains unknown.
10. **V02 closure evidence:** `PL-0269_CODEX_LOG_V02.md` preserves the V01 blocker history, records remediation and final gates, is a separate log-only publication and ends exactly `READY_FOR_INDEPENDENT_AUDIT`.
11. **Ordered continuation:** only after PL-0269 closes green, PL-0270 through PL-0288 execute in exact order under their existing frozen V01 prompts/criteria, with automatic continuation while green.
12. **Master evidence:** original M12 master log and remediation/continuation log accurately record child status, implementation/log SHAs, validation results and any limitations.
13. **Authority preservation:** Scan Master remains immutable; Design Model/library/assembly/freeform/flexible-pack authority separation, `METRIC_UNVERIFIED`, `DEFERRED_OWNER_VALIDATION` and no-manufacturing claims remain intact.
14. **Scope preservation:** no M13 CAD/BREP/OpenCascade/STEP work, unreviewed dependency, private evidence or silent/unlicensed asset import is introduced.
15. **Publication discipline:** implementation/evidence and child-log commits remain distinct; every completed child ends `READY_FOR_INDEPENDENT_AUDIT`.
16. **Final handoff:** successful completion records `BATCH_COMPLETED`, clean local/origin/GitHub parity, M13 not started and terminal `AWAITING_MILESTONE_AUDIT`. A real failure records exact `BATCH_STOPPED` frontier instead.

Independent audit must inspect actual GitHub source/diffs/evidence. Builder validation is not audit acceptance.
