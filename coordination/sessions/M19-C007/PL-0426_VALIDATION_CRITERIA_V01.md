# PL-0426 — Validation Criteria V01 (Claude, written before review)

1. Turntable angle events are bound to PackScan photo records deterministically by capture sequence and produce the existing turntable `capture_mode.parameters` (`frame_count`, `frame_index`, `angle_deg`).
2. No angle is ever invented. A photo with no event, several events, or a measured angle outside the tolerance stays unbound with a reason. Orphan events are reported.
3. Angle provenance is explicit: measured or commanded, plus the source ID. Angles are device-reported, not observed geometry, and calibration is pending.
4. The equivalent virtual-camera transform for a rotating object (station axis, PL-0397 frame) is correct and tested.
5. The module is hardware-agnostic and bounded. Without a turntable the existing workflow is unchanged (fallback). No device control, pairing or physical claim is made; PL-0425 hardware integration stays blocked.
