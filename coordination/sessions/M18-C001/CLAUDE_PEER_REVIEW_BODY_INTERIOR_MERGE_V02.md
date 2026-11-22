# CLAUDE_PEER_REVIEW V02: PR #34 (PL-0489), head 600be163
CI 45053570493 PASS. Local: 21 interior tests pass.

V01 HIGH fixed: 0.5/0.8/1.0/1.5/2.5 mm walls x 3 new seeds plus the original fixture all give deepest 60 for a 60 mm scan. Floor -> 97 mm, SCANNED_TO_FLOOR. Uniform floaters (50-800) are dropped; 3000 are refused.

## MEDIUM
- A different jar with a matching rim is refused only when the profile changes strongly. A 6 mm inset or a taper merges, reporting a 6-7 mm "wall" and writing the foreign points. The safe part: it reports deepest 0, so coverage is not over-claimed.

## LOW
- Dense reflection blobs pass the surface-support filter and are written; coverage is unaffected.
- An interior wall lying outside the body's outer wall (r42 vs r40) is not refused; it reports a 10 mm depth.

Verdict: PASS. Software scope only; physical accuracy needs real scans.
