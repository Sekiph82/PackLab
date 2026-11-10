"""PL-0390: STEP export round trip checked by a parser independent of the CAD kernel.

The export and the kernel reopen run through OCP (``validate_step_export_round_trip``).
This test re-reads the written ISO 10303-21 text with plain regular expressions, so the
unit, solid count, product name and dimensional extents are confirmed without OCP. The
fixture is a disposable synthetic revolve in a temp directory; STEP validity is not a
physical measurement or a mould/manufacturing approval.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from tests.core.test_cad_brep import _inputs

from packlab_core.cad_brep import revolve_design_model_to_brep
from packlab_core.cad_step_export import export_design_model_step
from packlab_core.reconstruction import ScaleState

_POINT = re.compile(r"CARTESIAN_POINT\(\s*'[^']*'\s*,\s*\(([^)]*)\)\s*\)")


def test_step_text_independently_confirms_units_solid_name_and_extents(tmp_path: Path) -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    representation = revolve_design_model_to_brep(model, profile, operation)
    path = tmp_path / "bottle.step"
    exported = export_design_model_step(model, representation, path, part_name="Bottle")
    kernel_report = exported.round_trip_validation
    text = path.read_text(encoding="ascii")

    assert text.startswith("ISO-10303-21;") and text.rstrip().endswith("END-ISO-10303-21;")
    assert "AUTOMOTIVE_DESIGN" in text  # AP214 schema
    assert re.search(r"SI_UNIT\(\s*\.MILLI\.\s*,\s*\.METRE\.\s*\)", text)
    assert len(re.findall(r"=\s*MANIFOLD_SOLID_BREP\(", text)) == 1
    assert re.search(r"PRODUCT\(\s*'Bottle'", text)

    points = [
        tuple(float(value) for value in match.group(1).split(","))
        for match in _POINT.finditer(text)
    ]
    points = [point for point in points if len(point) == 3]
    assert len(points) > 100
    width, depth, height = kernel_report.source_dimensions
    # Revolved about Z: every point lies inside the source cylinder, and the radial and
    # axial extents reach the source dimensions (software tolerance, not physical).
    radial = max(math.hypot(x, y) for x, y, _z in points)
    z_values = [z for _x, _y, z in points]
    tolerance = 1e-5
    assert abs(radial - width / 2) <= tolerance and abs(radial - depth / 2) <= tolerance
    assert abs((max(z_values) - min(z_values)) - height) <= tolerance
    assert kernel_report.reopened_dimensions == kernel_report.source_dimensions
