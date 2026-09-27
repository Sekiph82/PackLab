# PL-0209 Implementation Spec — Metric Scale Provenance and Uncertainty

Mandatory pre-read:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

## Rule

A reconstruction coordinate value is not millimetres until PackLab has explicit accepted physical scale evidence.

Backends may output internally consistent coordinates, monocular metric-depth estimates or ARKit world units. None of these automatically become M09 measurement authority.

## Required scale states

- RELATIVE
- METRIC_UNVERIFIED
- METRIC_VERIFIED

Only M09 calibration logic may promote to METRIC_VERIFIED.

## ScaleProvenance

Persist:
- source method;
- calibration observation IDs;
- physical reference value and declared units;
- estimated scale factor;
- residual/error metrics;
- rejected observations;
- algorithm version;
- input reconstruction revision;
- uncertainty representation;
- created timestamp;
- actor/process provenance.

## Accepted sources

The exact accepted sources are determined by M09 tasks. Candidate evidence includes validated printed/physical calibration markers and approved known-distance references.

A neural model's metric-depth output may be a diagnostic/prior, but it is not sufficient alone for METRIC_VERIFIED.

## Transform policy

Scale and axis normalization are non-destructive transforms until an explicitly versioned normalized captured-geometry asset is baked.

Original reconstruction output remains recoverable.

## AI boundary

AI_VISUAL_REFERENCE never receives measurement authority even if it is fitted to a metric OBB. Fitting a generated object into a measured box does not make its local neck/thread/base geometry measured.

## Tests

- relative input cannot be labeled mm;
- rejected calibration observations cannot silently contribute;
- scale factor application is deterministic;
- scale provenance survives project reopen;
- changing parent reconstruction invalidates derived scale;
- AI visual reference remains non-authoritative after metric scene transform.
