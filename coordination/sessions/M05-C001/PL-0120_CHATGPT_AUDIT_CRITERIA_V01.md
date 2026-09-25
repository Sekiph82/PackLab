# PL-0120 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Accepted PackScan/session architecture is reused rather than duplicated.
5. PL-0120 satisfies the frozen task scope.
6. Implement a SwiftUI/UIKit share-sheet bridge using the finalized `.packscan` URL as the shared item.
7. Expose export from the real finalized scan/history flow; never share the mutable session directory or unfinalized partial file.
8. Support standard installed destinations such as Files/iCloud Drive/AirDrop/other share targets through the system share sheet without app-specific destination assumptions.
9. Handle share cancellation, presentation failure, missing package, and package replacement/deletion safely.
10. Retain/export a stable finalized package until the share activity has finished, then clean only temporary share staging if one was required.
11. Add testable presentation/state seams for package eligibility, cancellation, completion and missing-file behavior without claiming a physical share target was executed on Windows.
12. Tests exercise the production-used transfer/finalization/UI seam, not only a disconnected helper.
13. Security/privacy claims are truthful and secrets never enter Git/logs/package evidence.
14. Full locked suite, relevant project checks and git diff --check pass truthfully.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
