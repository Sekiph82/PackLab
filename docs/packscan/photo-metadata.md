# PackScan per-photo metadata

`metadata/photos.json` contains one record for each authoritative image. The
record binds `image_path`, a stable `photo_id`, and a zero-based `sequence`.
Consumers must reject duplicate paths, IDs, or sequence numbers and must
require the sequence-ordered records to match the manifest's image payloads.

Focal length is in millimetres, exposure is in seconds, ISO is an integer
exposure index, and white balance is in kelvin. Each value uses a status of
`available`, `unavailable`, `not_recorded`, or `estimated`; unavailable values
are explicit and never replaced with guessed EXIF data. `source` identifies
whether the value came from EXIF, an iOS API, an operator, or a derived
calculation.

Orientation uses the image's stored-pixel convention and an optional clockwise
EXIF/device rotation of 0/90/180/270 degrees. Pixel dimensions are stored
dimensions, not a display-size claim.
