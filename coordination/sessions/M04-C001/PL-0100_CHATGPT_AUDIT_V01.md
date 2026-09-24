# PL-0100 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

## Independent finding

QualityDecisionEngine has deterministic hard-reject precedence and warning retention, but `rejectUnavailableClipping` is not actually enforced: unavailable clipping is only warned when the flag is false and is silently ignored when the flag is true. Frozen table-driven coverage for unavailable metrics and equality boundaries is also incomplete, and the engine is not yet the live candidate-frame authority.

## Required remediation

Preserve the existing model/policy work and connect it to the single accepted M03 production runtime: live candidate quality, authoritative pose/coverage, health-gated capture, immutable accepted-source transaction and structured diagnostics. Add the exact missing behavior/boundary tests from the frozen V01 criteria. Do not add parallel camera/AR/motion/session ownership.

PL-0100 remains unchecked.

Decision: **CHANGES_REQUIRED**
