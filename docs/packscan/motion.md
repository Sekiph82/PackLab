# PackScan CoreMotion metadata and synchronization

Motion uses the device right-handed axis convention `X` right, `Y` up, `Z`
forward. Attitude quaternions use `xyzw`; rotation rate is radians per second
and optional acceleration is metres per second squared. Every sample records a
UTC timestamp and CoreMotion source provenance.

Synchronization compares the same UTC domain to each photo capture timestamp.
The contract permits nearest-sample or linear interpolation, records the
tolerance in milliseconds, and records the source clock resolution. A sample
outside tolerance is `stale` or `out_of_window`, not silently reused. Missing
data is `unavailable`. The recorded clock resolution bounds any precision claim;
the schema never implies precision finer than the clocks support.
