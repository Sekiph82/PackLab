# CLAUDE_PEER_REVIEW -- PL-0425 software half (V02, re-review of V01 findings)

Reviewer: independent Claude Code review subagent. I am not the implementer. I made no source edits and no git writes; mutants and probes ran in a scratchpad copy outside the repo.
Scope: the software half only (SOFTWARE COMPLETE / PHYSICAL VALIDATION PENDING). The hardware gate (device make/model, protocol, e-stop wiring, calibration) stays open.

## Inputs (untracked at HEAD 4ee6bb09)
- core/src/packlab_core/turntable_driver.py sha256 84d3ca01cc01d8f2695055e14771357067b03d93e79667ca935c275498138c69 (913 lines)
- tests/core/test_turntable_driver.py sha256 c60f37612c201c82fb0cb220d9a462821078bad1acff1e5af90c882aef24f7e3

## Commands run by the reviewer
- pytest -q tests/core/test_turntable_driver.py tests/core/test_turntable_sync.py: 43 passed (this matches the implementer's count)
- ruff check and ruff format --check: clean. mypy on the module: no issues.
- Mutation suite: the 21 V01 mutants plus 12 new ones (N1-N12) targeting the fixes. 30 killed, 3 survived.
- Probe script exercising every fix through the public API.

## V01 finding disposition
- P2-1 FIXED. _run (l.~420) now catches Exception: it faults with reason transport_error:<type>, clears homed and token, and sends a best-effort STOP; a failing halt send is logged as HALT_SEND_FAILED. Probe: an OSError in receive mid-move gives FAULT, homed False, last frame STOP. When send also fails, the driver still ends in FAULT plus HALT_SEND_FAILED. Mutant N3 killed.
- P2-2 FIXED. Two new limitations are present. SINGLE_THREADED_NO_PREEMPTIVE_SOFTWARE_ESTOP states honestly that a request is honoured only between transport polls and that the device keeps executing until it gets the ESTOP frame. DEVICE_ROTATION_DIRECTION_UNVERIFIED is also present. The module docstring adds a Concurrency section. The new request_emergency_stop() only sets a threading.Event, so it is the only cross-thread entry and is safe to call from another thread. The request is checked in _run before the body and in _accept at every poll; when seen, it is cleared and turned into an estop abort, which latches and sends an ESTOP frame. Probes:
  - A request pending on an idle driver: the next rotate_to latches and sends only ESTOP, no MOVE.
  - A request raised mid-move: the frames on the wire are MOVE then ESTOP, and the driver ends ESTOP_LATCHED.
  - A request pending before connect: the driver latches and sends no frames.
  Mutants N1, N9 and N10 killed.
- P2-3 FIXED. Mutant M6 (_latch keeps the token) is now killed.
- P3-1 FIXED. _fail closes the transport and clears _connected on any failed connect, latched or not. Probe: after a failed reconnect while latched, _connected is False and connect() can be retried. If open() itself raises, the driver ends DISCONNECTED and unconnected. Mutant N4 killed.
- P3-2 FIXED. A device e-stop input asserted during connect latches: the driver ends ESTOP_LATCHED, stays connected, and sends an ESTOP frame. Mutant N5 killed.
- P3-3 FIXED. enabled=None reads the env flag (default off), and non-bool values raise enabled_invalid. Probes: "false" and 1 raise; None with the env unset gives feature_disabled; env true gives device mode. Mutants N6 and N7 killed.
- P3-4 FIXED. Mutant M10 (commanded/measured swap) is now killed.
- P3-5 FIXED. Mutant M21 (rejected Ack ignored) is now killed.
- P3-6 FIXED. DEVICE_ROTATION_DIRECTION_UNVERIFIED limitation added.
- P3-7 FIXED. SETTLING can now go back to the captured motion state (HOMING or MOVING) when a moving report arrives. This new edge in the _ALLOWED table is reachable only inside _await_position, so it does not open any command path. Motion commands still require IDLE + homed. Mutant N8 killed.

## Flagged behaviour (assessed)
A request_emergency_stop still pending once the driver is already latched is honoured on the next _run-based call. A reset_fault therefore fails with operator_software_estop: the token is consumed and the driver stays latched. A fresh acknowledgement plus a second reset then succeeds (probe g/g2). If the driver is disconnected, the request is honoured at the next connect instead. I consider this fail-safe and acceptable: a second e-stop press is never silently discarded.

## Remaining findings (new, all P3; none allows motion in FAULT/ESTOP)
- P3-A Test gap (mutant N2 survived). If the _run-level _check_estop_request is removed, the suite still passes. But that check is the only thing that stops a MOVE frame from being sent when a request is pending at command start; without it, the latch would happen only at the first poll, after MOVE is on the wire. The code is correct today (probe b shows only ESTOP sent). Add a test that pending request + rotate_to sends no MOVE/HOME frame.
- P3-B Test gap (mutant N11 survived). If the HALT_SEND_FAILED handler is removed, a second transport exception during the halt would escape _fail. No test pins this; probe a2 shows the handler works.
- P3-C Test gap (mutant N12 survived). If a failed connect stops closing the transport, no test notices.
- P3-D A request_emergency_stop on an idle driver is not visible in state until the next command (the docstring says so). A UI that reads driver.state right after the button press still sees IDLE. The table is not moving, so this is not unsafe; it is a UX/documentation note for the eventual operator UI.
- P3-E The catch-all in _run also converts internal driver bugs (for example an IllegalTransitionError) into a FAULT result with reason transport_error:<type>. That is fail-safe, but the reason label is misleading for non-transport errors.

## Mutation summary (temp copy)
Killed (30): M1-M21 (all V01 mutants, including the former survivors M6, M10, M21), N1, N3-N10.
Survived (3): N2, N11, N12 (P3-A..C).

## Verdict
SOFTWARE_PASS_WITH_NOTES. Every V01 P2 and P3 finding is fixed and verified against the source, by probes and by mutants. The remaining notes are P3 test-coverage and labelling items only. The software half can be recorded as SOFTWARE COMPLETE / PHYSICAL VALIDATION PENDING; PL-0425 itself stays unchecked until there is real device, protocol, hardware e-stop and calibration evidence.
