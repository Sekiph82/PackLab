# CLAUDE_PEER_REVIEW -- PL-0425 software half (V01)

Reviewer: independent Claude Code review subagent. I did not write the implementation or the tests. I made no source edits.
Scope: the software half only, recorded as SOFTWARE COMPLETE / PHYSICAL VALIDATION PENDING. The PL-0425 hardware gate stays open because the make/model, BLE/USB protocol and e-stop wiring are owner-gated.

## Inputs reviewed (untracked at HEAD 4ee6bb09)
- core/src/packlab_core/turntable_driver.py sha256 87414624001dda70d1a0660581c36dc44956d5fc6f0c41f40522fb71e269f32c
- tests/core/test_turntable_driver.py sha256 922104239d6bae4a196518553ce0252880cbb45c52302b47346fab30deeec233
- core/src/packlab_core/turntable_sync.py (PL-0426, unchanged), core/src/packlab_core/config.py (flag parsing)

## Commands run by the reviewer
- pytest -q tests/core/test_turntable_driver.py tests/core/test_turntable_sync.py: 37 passed
- ruff check and ruff format --check on the module and its test: clean
- mypy core/src/packlab_core/turntable_driver.py: no issues
- 21 mutations, applied to a copy of the package in a temp directory and never to the repo: 18 killed, 3 survived (details below)
- An edge-case probe script, also run outside the repo

## Verified correct
- Motion refusal. Two independent layers block motion. _require_idle (l.384) needs IDLE + homed, and the _ALLOWED table (l.87) has no FAULT/ESTOP/DISCONNECTED -> HOMING/MOVING edge. Every fault path clears _homed. The property test and the M2/M14 mutations confirm this. I found no path that sends MOVE/HOME while in FAULT/ESTOP_LATCHED/DISCONNECTED.
- Latch. emergency_stop latches in software before it sends anything (l.334). A disconnect keeps the latch (l.478). stop() never clears it. The latch is left only through reset_fault with a valid token. The token is consumed even on a failed attempt (l.359), compared with hmac.compare_digest, and cleared by _latch/_fail. Probe: a token acknowledged in FAULT is refused after a later e-stop. A reset while connected re-reads status and refuses if the device e-stop input is asserted. Re-homing is always required afterwards.
- Settle rule. It needs N consecutive reports that are in tolerance and not moving (l.557); a moving report or an out-of-tolerance one resets the run. The measured angle is the commanded angle plus the mean signed error, wrapped. _signed returns values in (-180, 180]. I verified the 0/360 wrap: 359.5 -> 0.0 settles at a measured 359.94, and the _norm mutation is killed.
- Anti-backlash. A counter-clockwise move first goes to target - anti_backlash and then approaches the target clockwise. The constructor enforces anti_backlash > 2*tol, so a stale pre-move report cannot satisfy either leg. The simulator backlash model makes the test discriminating (M5 killed).
- Convention. Increasing angle means clockwise as seen from above throughout. to_angle_event passes the commanded and measured angles straight through as TurntableAngleEvent with no sign change. That matches the clockwise_from_reference convention in turntable_sync. The end-to-end tests bind 24 and 36 stops as COMPLETE.
- Determinism. The simulator is fully seeded on a virtual clock. Acknowledgement tokens are random by design and never enter the events. The same-seed and different-seed tests pass.
- Feature flag. It is parsed the same way as config.py l.104-107 (case-insensitive true/false; anything else raises ConfigError) and defaults to off.
- Honesty. The module docstring and LIMITATIONS state that the system is simulation-only, that the hardware e-stop is NOT validated, that angles are not physically calibrated, and that link-loss behaviour is unverified. Every CommandResult and plan result carries these limitations. I found no overclaim of hardware capability.

## Findings

### P1
None.

### P2
- P2-1 turntable_driver.py:410-418: transport exceptions other than TurntableTransportDisconnected escape _run unhandled. Probe: an OSError raised from receive during rotate_to propagates. The driver is left in state MOVING with homed=True, and no STOP is sent; the last frame on the wire is MOVE. Motion is still refused, because the state is not IDLE, and emergency_stop can still latch from MOVING. But the device gets no best-effort halt, and the driver keeps an inconsistent homed flag. A real BLE/USB stack raises arbitrary exceptions, and the TurntableTransport Protocol does not document that only TurntableTransportDisconnected is allowed. Fix: catch Exception in _run, fault the driver, attempt a STOP, then re-raise or return a result. Alternatively, document a strict transport exception contract.
- P2-2 Missing limitation: the software e-stop cannot pre-empt an in-flight command. The driver is synchronous and not thread-safe (no lock). rotate_to/home block until settle or timeout, up to 15 s/30 s. A UI e-stop issued from another thread would race _state/_events. While a command runs, the only things that can interrupt it are the device e-stop input or a timeout. LIMITATIONS and the docstrings do not say this. Add a limitation such as SINGLE_THREADED_NO_PREEMPTIVE_SOFTWARE_ESTOP, or add a lock and a pre-empting abort flag.
- P2-3 Test gap on a safety invariant (mutation M6 survived). If _latch stops clearing the token (l.452), the suite still passes. The token-survives-new-latch case is correct in the code today (verified by probe), but no test pins it. Add: acknowledge in FAULT -> emergency_stop() -> reset_fault(old_token) must raise AcknowledgementRequiredError.

### P3
- P3-1 turntable_driver.py:459-473: a failed reconnect while ESTOP_LATCHED leaves _connected=True. In that state _fail takes the non-DISCONNECTED branch. Probe: when connecting to a silent device while latched, connect() returns status_timeout and later connect() calls raise already_connected. This is a liveness issue only; no motion is possible.
- P3-2 turntable_driver.py:459-463: a device e-stop input asserted during connect() is reported as CONNECT_FAILED / DISCONNECTED rather than ESTOP_LATCHED. This is safe, because the driver is disconnected, but the event log does not latch the e-stop.
- P3-3 turntable_driver.py:796,821: run_turntable_capture_plan(enabled=...) is not type-checked and does not read the env flag. Probe: enabled="false" (a truthy string) runs the plan in device mode. TurntableDriver is also usable directly without the flag. So the flag gates only callers that pass turntable_driver_enabled() explicitly; there is currently no such caller. Require enabled to be a bool, or default it to turntable_driver_enabled().
- P3-4 Test gap: mutation M10 survived. Swapping commanded and measured in to_angle_event (l.190) is not detected, because both values are within tolerance. Pin the field mapping with the scripted transport.
- P3-5 Test gap: mutation M21 survived. If a device-rejected Ack (accepted False, l.508) is ignored, no test fails. Add a scripted transport that rejects MOVE.
- P3-6 Limitations wording. The physical rotation direction of a real device (whether positive is actually clockwise from above) is unverified. It is implicitly covered by SIMULATION_ONLY, but it is worth listing explicitly for the hardware gate.
- P3-7 turntable_driver.py:541-556: SETTLING is entered on the first not-moving report and is never left if movement resumes (for example, ringing). This is cosmetic: settle samples still reset correctly.

## Mutation results (temp copy, not the repo)
Killed (18): token not consumed on failure; _require_idle state check removed; non-consecutive settle; _signed sign flip; anti-backlash removed; disconnect clears latch; flag default on; no STOP after fault; stall detection removed; measured not wrapped; reset skips e-stop-input check; fault keeps homed; mean error dropped; e-stop input ignored; stale reports not dropped; lenient flag; reset without acknowledgement; settle count N-1.
Survived (3): M6 _latch keeps token (P2-3); M10 commanded/measured swap in to_angle_event (P3-4); M21 rejected Ack ignored (P3-5).

## Verdict
SOFTWARE_PASS_WITH_NOTES. The safety state machine, the latch/token handling, the settle rule, the wrap handling, the convention and the determinism are correct, and the honesty statements are adequate. I recommend fixing P2-1 and P2-3 and adding the P2-2 limitation before recording SOFTWARE COMPLETE; none of them allows motion in FAULT/ESTOP. PL-0425 overall stays open as PHYSICAL VALIDATION PENDING (real device, protocol, hardware e-stop circuit, angle calibration).
