# CLAUDE_PEER_REVIEW - PL-0481 iOS five rings, strict order (PR #27, head 32d509bf) V01

Reviewer: Claude peer subagent (not the implementer). Evidence: diff origin/main...32d509bf, CI run 45023213814 (all 3 jobs success: 243/243 XCTests, E2E 2 scans x 80 images validate_packscan PASS); 45018798574/45020205783 failed on the old 16-wedge E2E/240 count, fixed honestly.

HIGH: none.

MEDIUM: none.

LOW
- M04CaptureEngine.swift allowsInOrder: first photo of a new ring may be ANY wedge; guidance targets the nearest, but the overlap with the previous ring is advisory only.
- Old sessions: config mismatch makes restoreM04OrbitCoverage return false, so coverage restarts; earlier photos stay in the session (exported, not counted). Acceptable, undocumented.
- Raw ids: chips show "h10".."h50"; hint appends "(capture_out_of_order)". Chips 17 pt high may clip at large Dynamic Type.
- Glossy/Jerrycan 12->16: density not reduced; test relaxed > to >= (legitimate, glossy no longer denser than matte).

Verified: manual and auto refusals, observe() never counts out of order, retake only of the last wedge (counted as duplicate), turntable unchanged and tested, no test removed (240+3), receiver assertion still exact (80). Python receiver/Studio have no ring-id dependency.

Verdict: PASS (owner device recapture still required to close PL-0481).
