"""Re-verify the hardened HEIC decode on the real Test-333 photos against the previous
(verified 24/28) build's decoded images: same pixels expected, new collision-safe names."""

import hashlib
import subprocess
import time
from pathlib import Path

from packlab_studio.build_model import find_ffmpeg, heic_decode_command, working_image_name

HEIC = Path(r"<USERPROFILE>\Documents\PackLab-work\test-333\heic")
PREVIOUS = next(
    Path(r"<USERPROFILE>\Documents\PackLab-work\studio-e2e-build").glob(
        "data-20261120-225515/projects/default/working/reconstruction/*/outputs/colmap/images"
    )
)
OUT = Path(r"<USERPROFILE>\Documents\PackLab-work\studio-e2e-build") / time.strftime(
    "heic-check-%Y%m%d-%H%M%S"
)
OUT.mkdir(parents=True)
ffmpeg = find_ffmpeg()
assert ffmpeg is not None, "ffmpeg not found"
print("ffmpeg:", ffmpeg, hashlib.sha256(ffmpeg.read_bytes()).hexdigest())
same = 0
sources = sorted(HEIC.glob("*.heic"))
for source in sources:
    target = OUT / working_image_name(source)
    subprocess.run(heic_decode_command(ffmpeg, source, target), check=True)
    previous = PREVIOUS / (source.stem + ".jpg")
    same += target.read_bytes() == previous.read_bytes()
print(f"decoded {len(sources)}; byte-identical to the verified build: {same}")
# A crafted "HEIC" that is really a playlist must not be followed.
evil = OUT / "evil.heic"
evil.write_text("#EXTM3U\n#EXTINF:1,\nhttp://127.0.0.1:9/x.ts\n", encoding="ascii")
result = subprocess.run(
    heic_decode_command(ffmpeg, evil, OUT / "evil.jpg"), capture_output=True, text=True
)
print("crafted playlist rc:", result.returncode, "| output written:", (OUT / "evil.jpg").exists())
print("stderr:", result.stderr.strip()[:200])
