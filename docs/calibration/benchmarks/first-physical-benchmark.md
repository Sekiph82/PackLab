# First physical calibration benchmark

This is the owner execution procedure for the first PackLab physical
calibration benchmark. It connects one physically verified printed mat to one
capture session and one benchmark record. It does not turn nominal SVG
geometry, synthetic tests, or an empty template into physical evidence.

## Required inputs and records

Before capture, the owner must have:

1. An exact public mat asset from [mat-assets.md](../mat-assets.md), with its
   source revision or SHA-256 recorded.
2. A completed copy of
   [verification-record-template.md](../verification-record-template.md) whose
   final status is `ACCEPTED_FOR_CAPTURE`. The benchmark record must link its
   stable record ID and retain the owner-controlled record outside public Git
   when it contains private provenance.
3. The blank
   [benchmark-record-template.md](benchmark-record-template.md), copied to an
   owner-controlled record for this session.

The nominal SVG values are source geometry only. The benchmark's known
dimension must come from the accepted owner-measured verification record. If
that record is missing, incomplete, or rejected, do not capture and leave the
benchmark status `OWNER_REQUIRED`.

## Capture procedure

1. Record the exact mat asset, source revision/hash, verification-record ID,
   mat attempt, printer/media context and the owner verification status.
2. Use the PL-0065 procedure: iPhone 16 Standard, back `main_wide_camera_1x`,
   exactly `1.0x`, no lens switching, original pixel dimensions, and no
   screenshot/crop/rescale. Record resolution, orientation, focus mode or
   device-reported focus distance, capture app version, calibration model and
   policy versions.
3. Record lighting, surface/background, camera-to-mat setup, approximate
   capture distance if available, and any conditions that could affect the
   images. Do not replace an unavailable field with an estimate.
4. Capture the seven PL-0065 views: fronto-parallel near, fronto-parallel
   far, yaw left, yaw right, pitch up, pitch down, and corner coverage with
   markers near image edges. Preserve original images and metadata in the
   owner's private evidence store.
5. Assign every candidate frame a stable sample ID. Run the real PackLab
   detector/scale/confidence path. Record every accepted, rejected, invalid,
   or unavailable sample in the benchmark record, including the reason. A
   rejected sample is never deleted or silently omitted from counts.
6. For each usable sample, estimate the verified marker-side dimension in mm
   (or another explicitly identified verified mat dimension) and calculate the
   errors using the formulas in the record template. The known dimension is
   the owner-measured value linked from the accepted verification record, not
   the nominal `40 mm` value unless the owner record independently measured and
   accepted it as `40 mm`.
7. Complete aggregate fields only from the recorded samples. Report accepted,
   rejected, invalid and missing-measurement counts separately. Do not invent
   an accuracy threshold from this first session; cite only the provisional
   mathematical consistency gates already documented in
   [confidence-thresholds.md](../confidence-thresholds.md).
8. Store private raw photos, device identifiers that are not needed for
   reproduction, and owner signatures outside public Git. Publish only safe
   record IDs, hashes/references, non-sensitive metadata and the resulting
   audit handoff when the owner authorizes it.

## Evidence boundary and completion

The owner controls the physical mat, printer output, ruler/caliper readings,
iPhone capture and private evidence references. Synthetic/public tests can
verify code contracts but cannot satisfy this benchmark. PL-0068 remains
`OWNER_REQUIRED` until an owner supplies both an accepted physical mat
verification record and a corresponding physical capture/measurement session.

The benchmark record must remain `UNRECORDED` or `OWNER_REQUIRED` while any
required physical field is absent. Do not mark it complete based on this
procedure, the SVG source dimensions, or builder test output.
