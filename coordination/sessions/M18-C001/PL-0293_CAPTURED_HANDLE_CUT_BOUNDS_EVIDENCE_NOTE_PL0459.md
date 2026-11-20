# Evidence note: PL-0293 captured handle-opening cut was effectively a no-op before PL-0459

- Author: Claude Code implementation agent (PL-0459, PR #17). This is a coordination evidence note. It does not edit or replace the accepted PL-0293 audit.
- Found by: wiring the jerrycan family in PR #17. Confirmed independently in CLAUDE_PEER_REVIEW_STUDIO_PACKAGE_FAMILIES_V01 (finding M1).

## Defect
`core/src/packlab_core/cad_boolean.py::_opening_tool` read `cad_shape_bounds()` (`Bnd_Box.Get()` = xmin, ymin, zmin, xmax, ymax, zmax, i.e. grouped) as interleaved (xmin, xmax, ymin, ...).

The extrusion start and span along the opening axis came from the wrong coordinates. On the accepted PL-0293 fixture (box x[0,1] y[0,4] z[0,8], x-axis opening 0.6 x 1.4):
- Before the fix, the cut removed 0.00084 mm^3, a ~1e-3 sliver at x ~ 0. The reviewer measured this on main.
- After the fix, it removes 0.84 mm^3: the full through-opening.

The accepted test `test_handle_opening_cut_is_deterministic_and_feature_linked` asserted provenance and determinism only, so it passed on the defective geometry. `_indent_tool` (grip indents) already used the grouped order and is unaffected.

## Fix and regression evidence (PR #17, branch feat/studio-package-families)
- `_opening_tool` now uses `lows = bounds[0:3]`, `highs = bounds[3:6]`.
- `tests/core/test_cad_boolean.py::test_handle_opening_cut_is_deterministic_and_feature_linked` now asserts:
  - removed volume = 0.6 * 1.4 * 1.0 (rel 1e-6);
  - the classifier returns OUT inside the opening at x = 0.02, 0.5 and 0.98 (through the whole body);
  - the classifier returns IN outside it.
- The assertion fails on the old code (removed volume 0.00084 vs expected 0.84) and passes on the fix.
- The standalone path (`cut_parametric_handle_opening`) is covered on a body centred at y = 0 (OUT at y = -15, 0, 15) in `tests/core/test_cad_parametric_handle_and_loft.py`.

## Consequences
- `operation_id` is unchanged, because it hashes provenance, not tool geometry.
- The cut BREP geometry digest and revision id change for the same inputs. No pinned ids or golden fixtures depended on the old values.
- No physical or mold claim was ever made for these cuts; status stays DEFERRED_OWNER_VALIDATION.
- PL-0293's acceptance record should be read with this note: the accepted captured cut produced the intended through-opening only from PR #17 onward.
