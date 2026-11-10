# PL-0418 — Validation Criteria V01

1. The policy identifies irreplaceable data, and states that the library backup service does not cover raw captures.
2. A concrete cadence (same-day, weekly, monthly restore drill, before change processes) is given and labelled as planning values needing site confirmation. 3-2-1 copies are required.
3. Copies are verified byte-for-byte by a reproducible manifest procedure. Missing, extra and altered files fail. Sample release depends on verified off-machine copies.
4. Security/privacy rules are included: no public Git or links, encryption, restricted access.
5. A synthetic dry-run of the verification tool is provided. No real storage, restore or Kenya library is claimed; PL-0412 stays separate.
