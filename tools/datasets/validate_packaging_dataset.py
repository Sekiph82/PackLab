"""Fail-closed validation for the deterministic synthetic M17 manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import zlib
from pathlib import Path, PurePosixPath


REQUIRED_FAMILIES = {"bottle", "jerrycan", "jar", "closure", "trigger_spray", "pump", "tube", "sachet"}
EXPECTED_MATERIALS = {"hdpe_matte", "pet_gloss", "pet_clear", "pp_translucent"}
MAX_MANIFEST_BYTES = 32 * 1024 * 1024
MAX_SAMPLE_BYTES = 32 * 1024 * 1024


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_reparse_point(path: Path) -> bool:
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        return True
    try:
        return bool(path.stat(follow_symlinks=False).st_file_attributes & 0x400)
    except (AttributeError, OSError):
        return False


def _png_integrity(path: Path, *, inspect_mask_coverage: bool = False) -> tuple[int, int, int, int, int]:
    if path.stat().st_size > MAX_SAMPLE_BYTES:
        raise ValueError(f"sample exceeds size cap: {path.name}")
    with path.open("rb") as stream:
        if stream.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"invalid PNG signature: {path.name}")
        width = height = color_type = None
        image_data = bytearray()
        saw_iend = False
        while not saw_iend:
            header = stream.read(8)
            if len(header) != 8:
                raise ValueError(f"truncated PNG chunk header: {path.name}")
            length, chunk_type = struct.unpack(">I4s", header)
            if length > MAX_SAMPLE_BYTES:
                raise ValueError(f"PNG chunk exceeds size cap: {path.name}")
            payload = stream.read(length)
            crc_bytes = stream.read(4)
            if len(payload) != length or len(crc_bytes) != 4:
                raise ValueError(f"truncated PNG chunk: {path.name}")
            expected_crc = struct.unpack(">I", crc_bytes)[0]
            if zlib.crc32(chunk_type + payload) & 0xFFFFFFFF != expected_crc:
                raise ValueError(f"PNG CRC mismatch: {path.name}")
            if chunk_type == b"IHDR":
                if length != 13:
                    raise ValueError(f"invalid PNG IHDR: {path.name}")
                width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
                if (width, height) != (640, 480) or bit_depth != 8 or compression != 0 or filtering != 0 or interlace != 0:
                    raise ValueError(f"unexpected PNG encoding or dimensions: {path.name}")
            elif chunk_type == b"IDAT":
                image_data.extend(payload)
            elif chunk_type == b"IEND":
                if length != 0:
                    raise ValueError(f"invalid PNG IEND: {path.name}")
                saw_iend = True
        if stream.read(1):
            raise ValueError(f"trailing data after PNG IEND: {path.name}")
    if width is None or height is None or color_type not in {2, 6}:
        raise ValueError(f"PNG must be RGB/RGBA with IHDR: {path.name}")
    bytes_per_pixel = {2: 3, 6: 4}.get(color_type)
    if bytes_per_pixel is None:
        raise ValueError(f"PNG must be RGB/RGBA with IHDR: {path.name}")
    stride = width * bytes_per_pixel
    expected_size = height * (stride + 1)
    try:
        decoder = zlib.decompressobj()
        raw = decoder.decompress(bytes(image_data), expected_size + 1)
    except zlib.error as exc:
        raise ValueError(f"invalid PNG image stream: {path.name}") from exc
    if len(raw) > expected_size or decoder.unconsumed_tail or decoder.unused_data or not decoder.eof:
        raise ValueError(f"PNG decompressed content exceeds or violates expected bounds: {path.name}")
    if len(raw) != expected_size:
        raise ValueError(f"unexpected decompressed PNG payload length: {path.name}")

    # Reconstruct scanlines to validate that the segmentation alpha contains
    # both background and object coverage. Anti-aliased edge pixels may be
    # fractional; this is a coverage mask, not a strict binary label.
    min_alpha, max_alpha = 255, 0
    previous_alpha = bytearray(width)
    for row_index in range(height):
        start = row_index * (stride + 1)
        filter_type = raw[start]
        if filter_type > 4:
            raise ValueError(f"unsupported PNG row filter: {path.name}")
        if inspect_mask_coverage:
            if color_type != 6:
                raise ValueError(f"segmentation mask must be RGBA: {path.name}")
            encoded = start + 1
            decoded_alpha = bytearray(width)
            for pixel in range(width):
                left = decoded_alpha[pixel - 1] if pixel else 0
                above = previous_alpha[pixel]
                upper_left = previous_alpha[pixel - 1] if pixel else 0
                if filter_type == 1:
                    predictor = left
                elif filter_type == 2:
                    predictor = above
                elif filter_type == 3:
                    predictor = (left + above) // 2
                elif filter_type == 4:
                    base = left + above - upper_left
                    distances = (abs(base - left), abs(base - above), abs(base - upper_left))
                    predictor = left if distances[0] <= distances[1] and distances[0] <= distances[2] else above if distances[1] <= distances[2] else upper_left
                else:
                    predictor = 0
                alpha = (raw[encoded + pixel * bytes_per_pixel + 3] + predictor) & 0xFF
                decoded_alpha[pixel] = alpha
                min_alpha = min(min_alpha, alpha)
                max_alpha = max(max_alpha, alpha)
            previous_alpha = decoded_alpha
    return width, height, color_type, min_alpha, max_alpha


def _validate_ply(path: Path) -> tuple[list[float], int, int]:
    if path.stat().st_size > MAX_SAMPLE_BYTES:
        raise ValueError(f"ground-truth PLY exceeds size cap: {path.name}")
    with path.open("r", encoding="ascii", newline="") as stream:
        if stream.readline().strip() != "ply" or stream.readline().strip() != "format ascii 1.0":
            raise ValueError(f"unsupported PLY header: {path.name}")
        units_seen = False
        vertex_count = face_count = None
        header = []
        while True:
            line = stream.readline()
            if not line:
                raise ValueError(f"unterminated PLY header: {path.name}")
            header.append(line.strip())
            if line.startswith("comment units meters;"):
                units_seen = True
            if line.startswith("element vertex "):
                vertex_count = int(line.split()[2])
            if line.startswith("element face "):
                face_count = int(line.split()[2])
            if line.strip() == "end_header":
                break
        if not units_seen or not vertex_count or not face_count:
            raise ValueError(f"invalid PLY units/element counts: {path.name}")
        lower = [float("inf")] * 3
        upper = [float("-inf")] * 3
        for _ in range(vertex_count):
            values = stream.readline().split()
            if len(values) != 3:
                raise ValueError(f"invalid PLY vertex record: {path.name}")
            coords = [float(value) for value in values]
            if any(not math.isfinite(value) for value in coords):
                raise ValueError(f"non-finite PLY vertex: {path.name}")
            lower = [min(lower[i], coords[i]) for i in range(3)]
            upper = [max(upper[i], coords[i]) for i in range(3)]
        for _ in range(face_count):
            fields = stream.readline().split()
            if not fields:
                raise ValueError(f"truncated PLY face list: {path.name}")
            count = int(fields[0])
            indices = [int(value) for value in fields[1:]]
            if count < 3 or count != len(indices) or any(index < 0 or index >= vertex_count for index in indices):
                raise ValueError(f"invalid PLY face index: {path.name}")
    bounds_mm = [round((upper[i] - lower[i]) * 1000.0, 6) for i in range(3)]
    return bounds_mm, vertex_count, face_count


def _validate_software_metric_bands(sample: dict, mesh_extent: list[float]) -> None:
    records = sample.get("expected_software_metric_bands")
    if type(records) is not dict:
        raise ValueError("expected software metric bands are missing")
    expected = {"segmentation_iou": (0.80, 1.0, "ratio"), "segmentation_dice": (0.88, 1.0, "ratio")}
    tolerance = sample["manufacturing_tolerance_mm_simulated"]["each_axis_plus_minus"][1]
    for axis, extent in zip("xyz", mesh_extent, strict=True):
        for stage in ("reconstruction", "parametric_fit"):
            expected[f"{stage}_extent_{axis}_mm"] = (max(0.0, extent - tolerance), extent + tolerance, "mm_simulated")
    if set(records) != set(expected):
        raise ValueError("expected software metric set is incomplete or contains unknown metrics")
    for key, (lower, upper, unit) in expected.items():
        record = records[key]
        if type(record) is not dict:
            raise ValueError(f"invalid expected metric record: {key}")
        if any(type(record.get(bound)) not in (int, float) or not math.isfinite(record[bound]) for bound in ("lower", "upper")):
            raise ValueError(f"expected metric bounds must be finite: {key}")
        if not math.isclose(record["lower"], lower, rel_tol=0, abs_tol=0.005) or not math.isclose(record["upper"], upper, rel_tol=0, abs_tol=0.005):
            raise ValueError(f"expected metric range differs from its declared synthetic scenario: {key}")
        if record.get("unit") != unit or record.get("provenance") != "SYNTHETIC_GENERATOR_SCENARIO" or record.get("authority") != "NONPHYSICAL_SOFTWARE_TEST_ONLY":
            raise ValueError(f"expected metric authority/provenance is invalid: {key}")


def validate_manifest(manifest_path: Path) -> dict:
    manifest_path = manifest_path.resolve(strict=True)
    if manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError("manifest exceeds size cap")
    root = manifest_path.parent.resolve(strict=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)
    if manifest.get("schema_version") != "1.0" or manifest.get("dataset_id") != "packlab-m17-synthetic-packaging-v2":
        raise ValueError("unsupported manifest identity/version")
    if manifest.get("fully_synthetic") is not True or manifest.get("physical_measurements_present") is not False:
        raise ValueError("synthetic/physical authority flags must be exact booleans")
    if manifest.get("owner_internal_use_scope") != "PackLab development/CI and owner-controlled design-office and future Kenya-factory use; no external reuse, sublicense, sale or marketing permission":
        raise ValueError("dataset-specific internal-use terms are missing or changed")
    samples = manifest.get("samples")
    if type(samples) is not list or len(samples) != len(REQUIRED_FAMILIES) * len(EXPECTED_MATERIALS) * 3:
        raise ValueError("unexpected sample count")
    identities: set[str] = set()
    folded_paths: set[str] = set()
    families: set[str] = set()
    materials: set[str] = set()
    for sample in samples:
        if type(sample) is not dict or sample.get("synthetic") is not True:
            raise ValueError("sample must be an explicitly synthetic object")
        if sample.get("measurement_authority") != "synthetic generator inputs only; no physical or Kenya ground truth":
            raise ValueError("sample measurement authority is missing or overstated")
        sample_id = sample.get("id")
        if type(sample_id) is not str or not sample_id.startswith("syn_") or sample_id in identities:
            raise ValueError("invalid or duplicate sample identity")
        identities.add(sample_id)
        family = sample.get("family")
        if family not in REQUIRED_FAMILIES:
            raise ValueError(f"unsupported package family: {family!r}")
        families.add(family)
        finish = sample.get("material_appearance", {}).get("finish")
        if finish not in EXPECTED_MATERIALS:
            raise ValueError(f"unsupported material appearance: {finish!r}")
        materials.add(finish)
        dimensions = sample.get("dimensions_mm_nominal_simulated")
        tolerance = sample.get("manufacturing_tolerance_mm_simulated", {}).get("each_axis_plus_minus")
        if type(dimensions) is not list or len(dimensions) != 3 or any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in dimensions):
            raise ValueError("invalid simulated dimensions")
        if type(tolerance) is not list or len(tolerance) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in tolerance):
            raise ValueError("invalid simulated tolerance")
        camera = sample.get("camera")
        if type(camera) is not dict or camera.get("model") != "pinhole plus Blender compositor lens distortion":
            raise ValueError("camera model metadata is missing")
        if camera.get("resolution_px") != [640, 480] or camera.get("sensor_fit") != "HORIZONTAL":
            raise ValueError("unsupported camera resolution or sensor fit")
        focal = camera.get("focal_length_mm")
        sensor = camera.get("sensor_mm")
        intrinsics = [camera.get(key) for key in ("fx_px", "fy_px", "cx_px", "cy_px")]
        if type(focal) not in (int, float) or not math.isfinite(focal) or focal <= 0 or type(sensor) is not list or len(sensor) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in sensor):
            raise ValueError("invalid camera lens/sensor metadata")
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in intrinsics):
            raise ValueError("invalid camera intrinsics")
        expected_focal_px = 640 * focal / sensor[0]
        if abs(intrinsics[0] - expected_focal_px) > 1e-5 or abs(intrinsics[1] - expected_focal_px) > 1e-5 or intrinsics[2:] != [320, 240]:
            raise ValueError("camera intrinsics do not match the declared sensor fit")
        matrix = camera.get("camera_to_world_row_major")
        if type(matrix) is not list or len(matrix) != 16 or any(type(v) not in (int, float) or not math.isfinite(v) for v in matrix):
            raise ValueError("invalid camera pose")
        if any(abs(matrix[12 + index] - expected) > 1e-6 for index, expected in enumerate((0, 0, 0, 1))):
            raise ValueError("camera pose is not a homogeneous transform")
        axes = [[matrix[row * 4 + col] for row in range(3)] for col in range(3)]
        for axis in axes:
            if abs(sum(component * component for component in axis) - 1) > 1e-4:
                raise ValueError("camera rotation axis is not unit length")
        if any(abs(sum(axes[a][i] * axes[b][i] for i in range(3))) > 1e-4 for a, b in ((0, 1), (0, 2), (1, 2))):
            raise ValueError("camera rotation axes are not orthogonal")
        determinant = (
            matrix[0] * (matrix[5] * matrix[10] - matrix[6] * matrix[9])
            - matrix[1] * (matrix[4] * matrix[10] - matrix[6] * matrix[8])
            + matrix[2] * (matrix[4] * matrix[9] - matrix[5] * matrix[8])
        )
        if abs(determinant - 1.0) > 1e-4:
            raise ValueError("camera pose rotation must be right-handed")
        if type(camera.get("blender_lens_distortion_factor_simulated")) not in (int, float) or not math.isfinite(camera["blender_lens_distortion_factor_simulated"]):
            raise ValueError("invalid simulated radial distortion")
        files = sample.get("files")
        if type(files) is not dict:
            raise ValueError("missing sample file map")
        image_records = {}
        for role in ("rgb", "mask"):
            file_record = files.get(role)
            if type(file_record) is not dict:
                raise ValueError(f"missing {role} path")
            rel = file_record.get("path")
            if type(rel) is not str or file_record.get("format") != "PNG":
                raise ValueError(f"invalid {role} file identity")
            path = PurePosixPath(rel)
            if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts) or "\\" in rel:
                raise ValueError(f"unsafe sample path: {rel!r}")
            folded = rel.casefold()
            if folded in folded_paths:
                raise ValueError("case-insensitive sample path collision")
            folded_paths.add(folded)
            resolved = root.joinpath(*path.parts)
            if any(_is_reparse_point(part) for part in [resolved, *resolved.parents] if part != root.parent) or not resolved.is_file():
                raise ValueError(f"missing or linked sample file: {rel}")
            try:
                resolved.resolve(strict=True).relative_to(root)
            except ValueError as exc:
                raise ValueError(f"sample path escapes dataset root: {rel}") from exc
            if type(file_record.get("bytes")) is not int or file_record["bytes"] != resolved.stat().st_size:
                raise ValueError(f"file byte length mismatch: {rel}")
            if type(file_record.get("sha256")) is not str or _sha256(resolved) != file_record["sha256"]:
                raise ValueError(f"file SHA-256 mismatch: {rel}")
            image_records[role] = _png_integrity(resolved, inspect_mask_coverage=role == "mask")
        if image_records["rgb"][:2] != image_records["mask"][:2]:
            raise ValueError(f"RGB/mask dimensions differ for sample {sample_id}")
        if image_records["mask"][2] != 6 or image_records["mask"][3] != 0 or image_records["mask"][4] != 255:
            raise ValueError(f"mask must have transparent background and opaque object coverage: {sample_id}")

        geometry = files.get("geometry")
        if type(geometry) is not dict or geometry.get("format") != "PLY":
            raise ValueError(f"missing PLY ground truth: {sample_id}")
        rel = geometry.get("path")
        if type(rel) is not str:
            raise ValueError(f"missing ground-truth geometry path: {sample_id}")
        geometry_path = PurePosixPath(rel)
        folded = rel.casefold()
        if geometry_path.is_absolute() or any(part in {"", ".", ".."} for part in geometry_path.parts) or "\\" in rel or folded in folded_paths:
            raise ValueError(f"unsafe or colliding geometry path: {rel}")
        folded_paths.add(folded)
        resolved_geometry = root.joinpath(*geometry_path.parts)
        if any(_is_reparse_point(part) for part in [resolved_geometry, *resolved_geometry.parents] if part != root.parent) or not resolved_geometry.is_file():
            raise ValueError(f"missing or linked PLY file: {rel}")
        try:
            resolved_geometry.resolve(strict=True).relative_to(root)
        except ValueError as exc:
            raise ValueError(f"geometry path escapes dataset root: {rel}") from exc
        if type(geometry.get("bytes")) is not int or geometry["bytes"] != resolved_geometry.stat().st_size or geometry.get("sha256") != _sha256(resolved_geometry):
            raise ValueError(f"PLY length/hash mismatch: {rel}")
        actual_bounds, vertices, faces = _validate_ply(resolved_geometry)
        expected_bounds = sample.get("expected_geometry_extent_mm")
        if type(expected_bounds) is not list or len(expected_bounds) != 3 or any(type(value) not in (int, float) or not math.isfinite(value) or not math.isclose(actual_bounds[axis], value, rel_tol=0, abs_tol=0.005) for axis, value in enumerate(expected_bounds)) or vertices != geometry.get("vertices") or faces != geometry.get("faces"):
            raise ValueError(f"PLY geometry metrics do not match manifest: {sample_id}")
        _validate_software_metric_bands(sample, actual_bounds)
        nominal = sample["dimensions_mm_nominal_simulated"]
        tolerances = sample["manufacturing_tolerance_mm_simulated"]["each_axis_plus_minus"]
        if any(abs(actual_bounds[axis] - nominal[axis]) > max(tolerances) for axis in range(3)):
            raise ValueError(f"generated mesh extent exceeds its simulated tolerance band: {sample_id}")
    if families != REQUIRED_FAMILIES or materials != EXPECTED_MATERIALS:
        raise ValueError("required family or appearance coverage is incomplete")
    return {"dataset_id": manifest["dataset_id"], "sample_count": len(samples), "families": sorted(families), "materials": sorted(materials), "manifest_sha256": _sha256(manifest_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate_manifest(args.manifest), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
