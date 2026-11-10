# PL-0428 Validation Criteria V01 — Adaptive Angle-Density Plan

1. Inputs pin sector-complexity evidence to one safe geometry revision ID and geometry SHA-256.
2. Sector intervals cover exactly `[0,360]` with no gaps/overlap; complexity values are finite in `[0,1]`.
3. Policy and total planned angles are bounded; per-sector count is a deterministic function of its score.
4. Planned angles lie strictly inside their sector, schedule order and plan ID are deterministic, and duplicate azimuths are absent.
5. Serialization is explicitly `PLANNED_NOT_OBSERVED`, non-authoritative and contains no raw geometry/path/owner data.
6. Tests use synthetic complexity evidence only. The module does not compute/validate geometric complexity or control hardware.
7. Exact local validation: `python -m pytest -q tests/core/test_adaptive_angle_plan.py` with `PYTHONPATH=core/src`.
8. `git diff --check` passes; no Actions/paid CI, PR, main source push, native build or release claim.
