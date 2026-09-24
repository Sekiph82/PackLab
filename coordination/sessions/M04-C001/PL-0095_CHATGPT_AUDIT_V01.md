# PL-0095 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

## Independent finding

MotionBlurAnalyzer correctly consumes MotionCaptureBinding semantics, but it is not wired into the live capture/runtime UI. The unavailable/stale reason path also contains a literal interpolation bug (`motion_(motion.status)`), and exact threshold-boundary coverage is missing.

## Required remediation

Preserve the existing deterministic algorithm work, close the specific defect/test gap above, and wire the metric into one production-used candidate-frame quality runtime that consumes actual capture-preview/candidate luminance and the existing M03 motion/session state. Do not create a second camera/sensor owner.

PL-0095 remains unchecked.

Decision: **CHANGES_REQUIRED**
