# PackLab A4 Printed-Mat Owner Verification — 2026-10-04

## Record identity

- record_version: `1.0.0`
- status: `ACCEPTED_FOR_CAPTURE`
- mat_asset: `assets/calibration/a4-packlab-calibration-mat.svg`
- printed_derivative: `PackLab_A4_Calibration_Mat_CLEAN.pdf` — textless print derivative preserving the canonical A4 calibration geometry
- canonical_source_blob_sha: `efeebcf45606cbb359c1165fbd04d0a1cc62143a`
- operator: `OWNER`
- measurement_session_date: `2026-10-04`
- measurement_timestamp_utc: `2026-10-04T12:16:00Z`
- printer_model: `UNRECORDED`
- media: `A4 paper`
- print_settings: `100% / Actual Size / no fit requested; printer UI state not separately retained; physical geometry verified below`
- instrument_type: `ruler`
- instrument_id_or_calibration_ref: `UNRECORDED`

## Nominal versus owner-measured geometry

The owner reported that every requested reading matched the nominal value exactly.  
Each required dimension was treated as repeated reading 1 / reading 2 from the owner-control session.

| Field | Nominal mm | Reading 1 mm | Reading 2 mm | Tolerance | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Page width | 210 | 210 | 210 | ±1.0 | PASS |
| Page height | 297 | 297 | 297 | ±1.0 | PASS |
| Marker side — upper-left / ID 0 geometry | 40 | 40 | 40 | ±0.5 | PASS |
| Marker side — upper-right / ID 1 geometry | 40 | 40 | 40 | ±0.5 | PASS |
| Reference bar | 100 | 100 | 100 | ±0.5 | PASS |
| Marker-centre distance X | 150 | 150 | 150 | ±1.0 | PASS |
| Marker-centre distance Y | 207 | 207 | 207 | ±1.0 | PASS |

## Decision

- scaling_gate: `PASS`
- failure_reason: `NONE`
- reprint_attempt: `0`
- reprint_action: `NOT_APPLICABLE`
- owner_measured_geometry_provenance: `owner-controlled physical ruler measurements on the printed A4 calibration mat, 2026-10-04`
- final_status: `ACCEPTED_FOR_CAPTURE`
- owner_signature_or_reference: `OWNER_CHAT_CONFIRMATION_2026-10-04`

## Scope and limitation

This record proves only that the printed A4 mat geometry passed the PackLab print-scaling gate.

It does **not** establish:

- camera calibration accuracy;
- marker-detector accuracy;
- scan/reconstruction dimensional accuracy;
- `METRIC_VERIFIED` status;
- mold/manufacturing suitability.

PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION` until the later owner-controlled physical benchmark requirements are completed and independently audited.
