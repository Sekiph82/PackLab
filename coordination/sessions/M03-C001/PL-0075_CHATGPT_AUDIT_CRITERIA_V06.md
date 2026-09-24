# PL-0075 — ChatGPT Remediation Audit Criteria V06

Task: **PL-0075 — White-balance physical-adapter evidence closure**

All criteria are mandatory.

1. M03-BATCH-006 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED and all 22 accepted M03 children remain unregressed.
3. Codex does not edit TASKS.md or ChatGPT audits and does not start M04.
4. Existing Batch-005 production camera composition is preserved.
5. PL-0075_CHATGPT_AUDIT_V05.md is fully addressed.
6. Use the same production-used injectable camera-device-control driver/seam as PL-0073/PL-0074 for AVFoundationWhiteBalanceAdapter behavior.
7. Preserve the current selected main-wide coordinator, runtime bridge, and accepted-photo metadata wiring.
8. Add behavior tests for wrong-device rejection, continuous-auto start, adjustingWhiteBalance stabilization, lock-before-stable failure, lock-after-stable success, actual observed temperature handling, runtime WB-state propagation, and persisted white-balance metadata.
9. No synthetic temperature/tint/gain may be represented as physical evidence; injected values are test fixtures only and must remain clearly synthetic.
10. Tests drive the production-used injectable device-control seam rather than a disconnected pure helper.
11. Focused/relevant regressions and git diff --check pass truthfully.
12. Child log records exact commits/files/results/limitations and uses full GitHub URLs in user-facing links.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
