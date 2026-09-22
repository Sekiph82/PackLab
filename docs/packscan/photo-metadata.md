# PackScan per-photo metadata

`metadata/photos.json` contains one record for each authoritative image. The
record binds `image_path`, a stable `photo_id`, and a zero-based `sequence`.
Consumers must reject duplicate paths, IDs, or sequence numbers and must
require the sequence-ordered records to match the manifest's image payloads.

Focal length is a positive finite JSON number with unit `mm`; exposure is a
positive finite JSON number with unit `s`; ISO is an integer from `1` through
`1000000` with the frozen unit token `iso`; and white balance is a JSON number
from `1000` through `100000` kelvin with unit `K`. JSON Schema's portable
numeric constraints are used; nonstandard keywords such as `finite` are not
used. Each value uses a status of `available`, `unavailable`, `not_recorded`,
or `estimated`; available and estimated values require value, unit, and
source, while unavailable and not-recorded values must not include a value.
Missing measurements are explicit and never replaced with guessed EXIF data.
`source` identifies whether the value came from EXIF, an iOS API, an operator,
or a derived calculation.

Orientation uses the image's stored-pixel convention and an optional clockwise
EXIF/device rotation of 0/90/180/270 degrees. Pixel dimensions are stored
dimensions, not a display-size claim.
