# PL-0097 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

## Independent finding

Shadow clipping correctly prefers object-region evidence when present, but the `warningFraction` threshold is likewise unused. Frozen tests do not cover normal/localized/broad/boundary cases completely, and the analyzer is not connected to live capture decisions.

## Required remediation

Preserve the existing deterministic algorithm work, close the specific defect/test gap above, and wire the metric into one production-used candidate-frame quality runtime that consumes actual capture-preview/candidate luminance and the existing M03 motion/session state. Do not create a second camera/sensor owner.

PL-0097 remains unchecked.

Decision: **CHANGES_REQUIRED**
