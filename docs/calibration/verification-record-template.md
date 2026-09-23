# PackLab printed-mat verification record template

Copy this template per print attempt. Replace bracketed fields only during an
owner-controlled physical measurement session. This repository version has no
fabricated measurements.

## Record identity

- record_version: `1.0.0`
- status: `UNRECORDED`
- mat_asset: `[A4 or A3 SVG path]`
- source_revision_or_sha256: `[ENTER SOURCE ID]`
- operator: `[ENTER OWNER/OPERATOR]`
- measurement_timestamp_utc: `[ENTER UTC TIMESTAMP]`
- printer_model: `[ENTER OR LEAVE UNRECORDED]`
- media: `[ENTER OR LEAVE UNRECORDED]`
- print_settings: `[100% actual size / record exact settings]`
- instrument_type: `[ruler or caliper]`
- instrument_id_or_calibration_ref: `[ENTER OR LEAVE UNRECORDED]`

## Nominal document geometry (copied from source, not measured)

| Field | Nominal mm | Owner measured mm — reading 1 | Owner measured mm — reading 2 | Tolerance | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Page width | `[210 or 297]` | `UNRECORDED` | `UNRECORDED` | `A4 ±1.0 / A3 ±1.5` | `UNRECORDED` |
| Page height | `[297 or 420]` | `UNRECORDED` | `UNRECORDED` | `A4 ±1.0 / A3 ±1.5` | `UNRECORDED` |
| Marker side — ID 0 | `40` | `UNRECORDED` | `UNRECORDED` | `±0.5` | `UNRECORDED` |
| Marker side — ID 1 | `40` | `UNRECORDED` | `UNRECORDED` | `±0.5` | `UNRECORDED` |
| Reference bar | `100` | `UNRECORDED` | `UNRECORDED` | `±0.5` | `UNRECORDED` |
| Marker-centre distance X | `[150 or 237]` | `UNRECORDED` | `UNRECORDED` | `±1.0` | `UNRECORDED` |
| Marker-centre distance Y | `[207 or 330]` | `UNRECORDED` | `UNRECORDED` | `±1.0` | `UNRECORDED` |

## Decision and reprint trace

- scaling_gate: `UNRECORDED`
- failure_reason: `[NONE RECORDED / ENTER OWNER OBSERVATION]`
- reprint_attempt: `[0 until an owner records an attempt]`
- reprint_action: `[NOT APPLICABLE / ENTER SETTINGS CHANGE]`
- owner_measured_geometry_provenance: `[instrument, operator, timestamp, mat attempt]`
- final_status: `UNRECORDED`
- owner_signature_or_reference: `[ENTER OWNER CONTROLLED REFERENCE]`

`ACCEPTED_FOR_CAPTURE` is prohibited while any required field remains
`UNRECORDED`. `REJECTED_SCALING` requires retaining the failed record and
creating a new attempt after correcting print settings.
