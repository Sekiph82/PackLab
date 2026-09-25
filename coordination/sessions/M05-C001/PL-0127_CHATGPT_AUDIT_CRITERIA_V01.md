# PL-0127 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing PackScan validation/session authority is reused rather than duplicated.
5. PL-0127 satisfies the frozen scope.
6. Create a PackLab Studio ingest application/controller boundary for `.packscan` paths that will later plug into the M06 PySide6 shell without starting M06 now.
7. Expose both dropped-path intake and file-picker-selected-path intake through the same authoritative import service; do not duplicate validation/import logic.
8. Accept only `.packscan` files, reject directories/multiple unsupported types deterministically, and normalize Windows paths safely without modifying the source.
9. Provide a minimal Windows-native/file-picker adapter seam and deterministic test fake so the flow is executable/testable now and visually wireable by M06 later.
10. Return structured import results/errors suitable for Capture Inbox UI rather than printing ad-hoc text.
11. Add tests for valid selected file, valid dropped file, multiple drop ordering, unsupported extension, directory, missing path and duplicate selection.
12. Tests exercise the production-used ingest/receiver/raw-store seam, not only isolated helpers.
13. Invalid/incomplete/untrusted data never reaches normal imported authority.
14. Privacy/secrets/private paths are handled truthfully and safely.
15. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
16. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
17. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
