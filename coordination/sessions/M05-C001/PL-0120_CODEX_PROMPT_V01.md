# PL-0120 — Codex Work Order V01

Task: **PL-0120 — iOS Share Sheet export**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0120_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0120_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0120_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03 and M04 must remain accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M06.

Reuse the accepted M02 PackScan contracts and M03/M04 session/finalization architecture. Do not create parallel package writers, camera/session owners or mutable export formats.

## Mandatory implementation

1. Implement a SwiftUI/UIKit share-sheet bridge using the finalized `.packscan` URL as the shared item.
2. Expose export from the real finalized scan/history flow; never share the mutable session directory or unfinalized partial file.
3. Support standard installed destinations such as Files/iCloud Drive/AirDrop/other share targets through the system share sheet without app-specific destination assumptions.
4. Handle share cancellation, presentation failure, missing package, and package replacement/deletion safely.
5. Retain/export a stable finalized package until the share activity has finished, then clean only temporary share staging if one was required.
6. Add testable presentation/state seams for package eligibility, cancellation, completion and missing-file behavior without claiming a physical share target was executed on Windows.

## Validation

Add behavior-bearing success, failure, cancellation, restart and exact-boundary tests appropriate to the task. Run focused tests, the full declared locked suite, relevant iOS/static/project checks, `git diff --check`, protected-file checks, and privacy/signing/secret review. Native iPhone/Xcode/network hardware claims may be made only if genuinely executed.

Create one implementation/evidence commit and then a separate child log-only commit. Every user-facing repository link must be a full GitHub URL, never a local filesystem path.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
