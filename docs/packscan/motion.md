# PackScan CoreMotion metadata and synchronization

Motion uses the device right-handed axis convention `X` right, `Y` up, `Z`
forward and freezes `CMAttitudeReferenceFrame.xArbitraryZVertical` as the
reference frame. Attitude quaternions use `xyzw`; rotation rate is radians per
second and optional acceleration is metres per second squared. Every sample
preserves the native CoreMotion monotonic timestamp in seconds since device
boot, plus its mapped UTC/photo timestamp and CoreMotion source provenance.

The photo/capture clock is a separate UTC domain. Synchronization records the
anchor and frozen equation `utc = anchor_utc + (native_s - anchor_native_s)`:
native CoreMotion seconds since boot are related to the anchor UTC timestamp,
with measured mapping uncertainty and resolution in milliseconds. The selected
nearest-sample or linear-interpolation association also records a tolerance in
milliseconds; a sample outside tolerance is `stale` or `out_of_window`, never
silently reused. The uncertainty, resolution, and tolerance bound any
precision claim; the schema never implies precision finer than the evidence.

`available` samples require attitude and rotation-rate payloads. `stale` and
`out_of_window` remain explicit association states. `unavailable` samples carry
the native timestamp and provenance but must not carry valid attitude, rotation
rate, or acceleration vectors. CoreMotion units are preserved, and this public
contract does not claim native device execution.
