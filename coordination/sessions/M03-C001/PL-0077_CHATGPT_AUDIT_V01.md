# PL-0077 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `08c1e0aa9823fcbaf081db7f6857b7c20eb96c2c`

## Independent findings

The child provides a useful deterministic recovery state machine with:
- start/running/interrupted/restarting/denied/restricted/unavailable/failed states;
- bounded restart attempts;
- permission/interruption/runtime-error events;
- actionable message strings;
- transition tests.

But the frozen task requires actual camera-error recovery, not only a standalone policy model.

### No real camera/session event integration

The implementation does not subscribe to or bridge actual NextLevel/AVFoundation session interruption, interruption-ended, runtime error, or permission change signals into the state machine. It therefore does not demonstrate real recovery behavior.

### Duplicate session/listener prevention is not implemented

There is no inspected listener/session ownership code proving repeated SwiftUI lifecycle events cannot register duplicate observers or create duplicate camera sessions. Criterion 11 is not satisfied by the pure state machine alone.

### Accepted/in-flight capture preservation is unproven

No integration exists between recovery events and `AcceptedStill` / the in-flight still-capture service. The child does not prove that already-accepted immutable captures survive recovery or that a failed in-flight request cannot be incorrectly accepted. Criterion 12 is not satisfied.

### User messages are not surfaced

`userMessage` exists as a computed string, but no UI/view-model binding exposes the recovery state/messages to the user.

## Criteria

- PASS: 1-10, 14, 16-18
- FAIL: 11, 12, 13, 15, 19-20

## Required remediation

1. Wire real AVFoundation/NextLevel permission, interruption, interruption-ended and runtime-error events into one camera recovery owner.
2. Make observer/session registration idempotent across repeated lifecycle events.
3. Integrate recovery with in-flight capture cancellation/failure and accepted immutable capture preservation.
4. Surface recovery/permission states in the capture UI/view model.
5. Add deterministic integration tests using injected camera-event sources and capture-state fixtures.
6. Publish a complete task-specific log checkpoint.

PL-0077 remains unchecked.

Decision: **CHANGES_REQUIRED**
