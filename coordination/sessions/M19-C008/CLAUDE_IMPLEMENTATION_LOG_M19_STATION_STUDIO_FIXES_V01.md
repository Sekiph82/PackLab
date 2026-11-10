# Claude implementation log — M19 station/Studio review fixes (V01)

Date: 2026-11-10. Implementer: Claude Code. This is not a review. It responds to
`CLAUDE_PEER_REVIEW_M19_STATION_AND_STUDIO_V01.md`.

| Finding | Change |
| --- | --- |
| P2-1 (PL-0428) | After rounding, every planned angle must lie strictly inside its sector and be distinct. A sector too narrow for its count fails closed with `sector_too_narrow_for_planned_angles`. |
| P2-2 (PL-0428) | New tests cover: plan ID bound to the geometry digest; invalid digests; 0/360 coverage; duplicate sector IDs; the score-to-count rounding table (7 pinned values); the narrow-sector case. |
| P2-3 (PL-0431) | New tests cover: Scan Master manifest authority (`authority_class`, `mold_use_authorized`, physical-accuracy status, geometry digest); the digest half of `is_exactly_scan_fitted`; the combo-box ghosting guard on the real user path. |
| P2-4 (PL-0431) | `_ghost_composite` now uses Qt's native colour mask (`createMaskFromColor` + `QBitmap`) instead of a per-pixel Python loop. A 1600×900 composite is tested to finish in under 0.5 s and is checked pixel by pixel against the background and geometry. |
| P3 (PL-0431) | A refused ghosting attempt keeps the `REVIEW ONLY · NON-AUTHORITATIVE` banner. The preview caption now says "caller-supplied, unverified". |
| P2-5 (PL-0434) | The test records the real `QPainter.drawText` calls during export. It asserts that the disclaimer, all 16 field labels, every `value  [provenance]` tag and the asset revision are actually painted. Removing the disclaimer draw call now fails the test (mutation verified). |

Accepted at prototype tier without code change: PL-0427, PL-0432 and PL-0433. All six modules are
**components only and not yet routed** into a Studio workflow; the existing workflow is the fallback.

Not addressed (P3):
- PL-0427 normalization edge cases;
- unvalidated public constructors in PL-0432;
- 6-significant-digit formatting in PL-0433;
- PL-0434 offscreen text layer and non-deterministic PDF bytes.

Hardware, turntable, station and physical gates stay pending.
