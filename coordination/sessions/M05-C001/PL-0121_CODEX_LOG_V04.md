# PL-0121 — Codex Implementation Log V04

Task: PL-0121 — Fix Swift negative decoder matrix for all V1 wire models  
Repository: https://github.com/Sekiph82/PackLab  
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CHATGPT_AUDIT_CRITERIA_V04.md  
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CHATGPT_AUDIT_V03.md

## Boundary and synchronization

- Starting synchronized commit: `8487b50`.
- Implementation/evidence commit: `330800e`.
- `TASKS.md` and ChatGPT audit artifacts were not edited.
- Scope was limited to the typed Swift negative decoder matrix.

## Implementation

- Replaced the prior status-only malformed loop with explicit negative cases for `TransferStatusMessage`, `TransferControlMessage`, `TransferCompletionAcknowledgement` and `TransferErrorEnvelope`.
- Each production type now has wrong protocol-name and unsupported-version assertions with stable `TransferWireError.malformed` and `TransferWireError.unsupportedVersion` expectations.
- The shared golden fixture and positive Python/Swift round-trip coverage were preserved.

## Validation

- `git diff --check`: passed.
- Focused transfer/TLS/wire Python suite: `12 passed`.
- Full locked Python suite: one Windows liveness test was initially flaky (`218 passed, 4 skipped, 1 deselected, 2 warnings`); isolated rerun passed (`1 passed`).
- Xcode/iOS XCTest execution: unavailable on this Windows host; typed Swift XCTest execution is not claimed.
- No physical-device or external-network evidence is claimed. No secrets, private keys, signing material or private scans were added.

## Handoff

The source and evidence are ready for independent inspection against the frozen V04 criteria.  
READY_FOR_INDEPENDENT_AUDIT
