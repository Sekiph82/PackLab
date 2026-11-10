# PL-0379 — Validation Criteria V01

1. Corrupt/truncated `.packscan` evidence is rejected by the actual import boundary.
2. Traversal or reparse payloads cannot escape the disposable extraction root.
3. Any quarantine path and diagnostic are verified from implementation/tests; do not assume unsupported behavior.
4. Test artifacts are isolated and contain no owner/private dataset content.
5. Test execution is deferred to M17 milestone end.
