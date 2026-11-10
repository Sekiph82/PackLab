# PL-0369 Owner Decision — Public CI Golden Subset

Date recorded: 2026-11-10

Question put to the owner in the Claude Code session: "May an 8-sample synthetic PL-0369 subset go in the public repo for CI?"
Owner answer: "Yes, commit subset".

## Scope recorded

- Permitted: committing a small subset (8 samples, one per package family) of the PackLab-generated synthetic M17
  benchmark (`packlab-m17-synthetic-packaging-v2`) to the public `Sekiph82/PackLab` repository under
  `tests/fixtures/m17_golden_subset/`, for CI and software regression use.
- The subset consists only of PackLab-generated procedural renders, masks and meshes. It contains no third-party
  source data (no YCB, Objectron or ABO content), no Kenya data, no supplier data and no physical measurements.
- This decision narrows the 2026-11-04 internal-use terms (`PL-0369_OWNER_DECISION_INTERNAL_USE_V01.md`) for this
  subset only: being in a public repository makes it publicly downloadable. It does not grant sale, sublicensing,
  marketing or trademark rights, and it does not change the terms of the full local dataset, which stays outside Git.
- No formal legal review is claimed.
