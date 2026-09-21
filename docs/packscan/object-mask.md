# Optional PackScan object masks

Masks are derived, optional payloads. An omitted `masks` entry is valid and
never reduces the authority of the original image. When present, a mask is a
grayscale 8-bit PNG with no alpha or palette, the same top-left pixel-centre
origin as its source image, and exactly the same width and height. Binary masks
use 0 for background and 255 for foreground; label masks use 0 for background
and a documented non-zero label index.

Each mask names its source image path and stable photo ID. Runtime validation
must resolve both against the manifest/photo metadata and reject a dimension
mismatch or linkage to a different photo. A mask is never measurement truth and
cannot replace an original capture.
