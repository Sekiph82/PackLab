# PackLab printable calibration mats

The source assets are vector SVG files with millimetre viewBox coordinates:

- `assets/calibration/a4-packlab-calibration-mat.svg` — page `210 x 297 mm`,
  marker side `40 mm`, marker-centre reference distances `150 x 207 mm`.
- `assets/calibration/a3-packlab-calibration-mat.svg` — page `297 x 420 mm`,
  marker side `40 mm`, marker-centre reference distances `237 x 330 mm`.

Both use the selected `DICT_APRILTAG_36h11` family and IDs `0..3`, which are
inside PackLab's active reserved range. The source metadata attributes are
machine-checked by `tests/calibration/test_calibration_mats.py`.

## Printing and physical verification

Print the SVG at exactly 100% / actual size. Disable “fit to page”, “scale to
media”, auto-rotation that changes the page, and any printer-driver scaling.
The black 100 mm nominal reference bar is an operator verification aid: after
printing, measure it and the labeled marker dimensions with a ruler or caliper
and record the result using the later pre-use verification procedure. The
nominal SVG dimensions alone do not establish printer accuracy, camera
accuracy, scale accuracy, or physical acceptance.

The four black/white marker matrices are deterministic vector encodings of
IDs 0, 1, 2, and 3 in `DICT_APRILTAG_36h11`; their known square geometry is
40 mm in the source coordinate system. No physical mat has been printed or
verified by this builder pass.
