# Calibration profile storage and invalidation

PackLab stores calibration profiles as versioned records keyed by the exact
capture configuration that produced them. The compatibility check is
deterministic and fail-closed: if PackLab cannot prove compatibility, the
profile is not reusable.

## Profile key

The required key dimensions are:

- device model;
- lens identity;
- camera position;
- image width and height in `px`;
- image orientation;
- zoom factor, unitless;
- focus mode;
- capture app version;
- calibration model version;
- calibration policy version.

Changing any non-resolution key dimension invalidates the profile. A resolution
change invalidates the profile unless the stored profile explicitly uses
`uniform_scale_about_origin` and the requested resolution has the same aspect
ratio. The default policy is `exact_reference_only`.

## Stored evidence

Profile records store:

- schema version;
- profile ID;
- creation timestamp in UTC `Z` format;
- verification timestamp in UTC `Z` format;
- provenance strings for source, device/native evidence status, and policy;
- calibration-quality evidence: confidence status, confidence score,
  reprojection RMSE in `px`, and accepted view count;
- units for image dimensions, zoom factor, and reprojection error.

This repository does not contain an owner-produced physical calibration
profile. Stored `candidate` or `measured` records require owner-device capture
and owner physical measurement evidence from PL-0065/PL-0068 workflows.
Runtime reuse validates the persisted profile shape against
`schemas/packscan/calibration-profile.schema.json` before compatibility
decisions. A reusable profile must also carry:

- `source = owner_physical_session`;
- `native_capture_evidence = owner_device`;
- `physical_measurement_evidence = owner_completed`;
- real RFC3339 UTC `created_at` and `verified_at` timestamps ending in `Z`;
- positive image dimensions and zoom factor;
- non-empty required key strings;
- known schema version and resolution policy;
- confidence score in `[0, 1]`, non-negative reprojection RMSE, and at least
  one accepted view.

Unavailable or placeholder provenance is retained as evidence that reuse is not
allowed; it is never silently promoted to compatibility.

## Reuse states

- `compatible`: profile may be reused for the request.
- `invalid`: profile must not be reused; reasons identify the changed
  dimension or malformed stored evidence.

There is no silent fallback. Unknown schema versions, unknown resolution
policies, rejected quality, unavailable provenance, malformed timestamps,
invalid dimensions, out-of-range quality fields, malformed units, and
incompatible key changes all return `invalid`.
