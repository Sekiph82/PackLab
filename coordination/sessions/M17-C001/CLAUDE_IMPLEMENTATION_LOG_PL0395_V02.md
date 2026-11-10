# Claude implementation log — PL-0395 freeze (V02)

Date: 2026-11-10. Implementer: Claude Code. This is not a review.

- Froze `docs/development/V1_LIMITATIONS_AND_MANUFACTURING_BOUNDARY.md` as revision 1.0 and added a revision-history table.
- Corrected the outdated recovery statement. The core orchestrator now resumes from verified checkpoints (PL-0380), but Studio does not persist those checkpoints, so restart after an application crash is not demonstrated.
- Added the limits of the advisory QA texture check and the rescan decision tree. Both are calibrated only on synthetic data.
- Added the CI guard `tests/ci/test_v1_limitations_freeze.py` (4 tests). It checks:
  - the exact no-direct-mold statement and the frozen revision;
  - that all 12 required gap families are present;
  - that the scale vocabulary matches `ScaleState` and `mm_unverified`;
  - that claim words are always qualified.
- No physical, hosted-release, legal or Kenya acceptance is claimed. The legal and owner release gates remain separate.
