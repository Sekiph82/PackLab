# PL-0096 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

## Independent finding

Highlight clipping analysis exists and handles localized versus broad clipping, but the configured `warningFraction` is never used in the decision calculation. The live candidate-frame quality pipeline is also not wired, so preset-specific highlight policy cannot affect actual capture yet.

## Required remediation

Preserve the existing deterministic algorithm work, close the specific defect/test gap above, and wire the metric into one production-used candidate-frame quality runtime that consumes actual capture-preview/candidate luminance and the existing M03 motion/session state. Do not create a second camera/sensor owner.

PL-0096 remains unchecked.

Decision: **CHANGES_REQUIRED**
