# PackLab pre-use printed-mat verification

This procedure verifies print scale and mat geometry before a physical capture.
It does not establish camera accuracy, detector accuracy, or measurement
accuracy. Only an owner-controlled physical measurement session may complete
the blank record template.

## Procedure

1. Select the exact SVG asset and record its source revision/hash in the
   record. Print at 100% / actual size with fit-to-page, scale-to-media,
   borderless expansion, and automatic resizing disabled. Do not use a PDF
   viewer or printer driver that silently rescales the page.
2. Record printer, media, print settings, instrument type and instrument ID.
   Use a ruler for the 100 mm bar and a calibrated ruler or caliper for the
   40 mm marker sides and the labeled centre-to-centre distances. Measure at
   least the reference bar, two marker sides, and both horizontal/vertical
   marker-centre distances. Repeat each dimensional reading twice and record
   both readings; do not replace missing readings with an estimate.
3. For A4, compare nominal page `210 x 297 mm`, marker side `40 mm`, bar
   `100 mm`, and centre distances `150 x 207 mm`. For A3, compare nominal page
   `297 x 420 mm`, marker side `40 mm`, bar `100 mm`, and centre distances
   `237 x 330 mm`. Coordinates are SVG millimetres with origin at the top-left
   page corner; centre distances are absolute differences between marker
   centres, not edge gaps.
4. Apply the print-geometry gate: marker side and bar readings must be within
   `±0.5 mm` of their nominal values; each centre-distance reading must be
   within `±1.0 mm`; page dimensions must be within `±1.0 mm` for A4 and
   `±1.5 mm` for A3. These are provisional print-scaling tolerances, not an
   accuracy claim for the camera or calibration algorithm.
5. If any reading is outside tolerance, mark the record `REJECTED_SCALING`,
   do not use the mat, check actual-size/no-fit settings and media selection,
   and reprint. A reprint receives a new record or a new attempt section; the
   failed record is retained. Do not edit measurements to obtain acceptance.
6. Mark `ACCEPTED_FOR_CAPTURE` only when every required field and repeated
   measurement is present and inside the print-geometry gate. A blank,
   `UNRECORDED`, or instrument-invalid field cannot produce acceptance.

## Nominal versus owner-measured geometry

The SVG source metadata is nominal document geometry. The record's
`owner_measured_geometry` section is the only place for physical readings. A
nominal `40 mm` marker or `100 mm` bar is not evidence that a printer produced
that size. No owner readings are included in this repository; the template
intentionally contains placeholders and `UNRECORDED` status.

Use [verification-record-template.md](verification-record-template.md) for
each printed mat and keep the completed owner record with the physical mat's
provenance. Do not include private scans, serial numbers unnecessary for
reproduction, credentials, or confidential supplier data in a public copy.
