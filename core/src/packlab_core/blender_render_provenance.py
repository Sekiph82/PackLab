"""Canonical, path-free provenance records shared by M14 still and GLB outputs."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

M14_RENDER_PROVENANCE_CONTRACT = "packlab.m14-render-provenance.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+!-]{0,63}$")


class BlenderRenderProvenanceError(ValueError):
    """Raised when canonical M14 provenance is incomplete or unsafe."""


def create_m14_render_provenance(
    *,
    packlab_commit: str,
    packlab_version: str,
    blender_executable_sha256: str,
    blender_build: Mapping[str, object],
    scene_package_revision_id: str,
    scene_package_sha256: str,
    source_revisions_and_digests: Mapping[str, object],
    render_engine: str,
    render_device: str,
    render_settings: Mapping[str, object],
    camera_light_preset_ids: Sequence[str],
    outputs: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Build deterministic shared provenance without copying ambient paths or time."""
    if not isinstance(packlab_commit, str) or not _COMMIT.fullmatch(packlab_commit):
        raise BlenderRenderProvenanceError("render_provenance_packlab_commit_invalid")
    if not isinstance(packlab_version, str) or not _VERSION.fullmatch(packlab_version):
        raise BlenderRenderProvenanceError("render_provenance_packlab_version_invalid")
    if not _is_sha256(blender_executable_sha256):
        raise BlenderRenderProvenanceError("render_provenance_blender_executable_digest_invalid")
    if not isinstance(blender_build, Mapping) or not _valid_blender_build(blender_build):
        raise BlenderRenderProvenanceError("render_provenance_blender_build_invalid")
    if not _is_revision(scene_package_revision_id) or not _is_sha256(scene_package_sha256):
        raise BlenderRenderProvenanceError("render_provenance_scene_package_invalid")
    if not isinstance(source_revisions_and_digests, Mapping) or not source_revisions_and_digests:
        raise BlenderRenderProvenanceError("render_provenance_source_bindings_invalid")
    if not isinstance(render_engine, str) or not render_engine or len(render_engine) > 64:
        raise BlenderRenderProvenanceError("render_provenance_engine_invalid")
    if not isinstance(render_device, str) or not render_device or len(render_device) > 64:
        raise BlenderRenderProvenanceError("render_provenance_device_invalid")
    if not isinstance(render_settings, Mapping) or not render_settings:
        raise BlenderRenderProvenanceError("render_provenance_settings_invalid")
    if not isinstance(camera_light_preset_ids, Sequence) or isinstance(
        camera_light_preset_ids, (str, bytes)
    ):
        raise BlenderRenderProvenanceError("render_provenance_preset_ids_invalid")
    if any(not _is_revision(item) for item in camera_light_preset_ids):
        raise BlenderRenderProvenanceError("render_provenance_preset_id_invalid")
    if not isinstance(outputs, Sequence) or isinstance(outputs, (str, bytes)) or not outputs:
        raise BlenderRenderProvenanceError("render_provenance_outputs_invalid")

    normalized_sources = _safe_json_mapping(source_revisions_and_digests)
    normalized_settings = _safe_json_mapping(render_settings)
    normalized_build = _safe_json_mapping(blender_build)
    normalized_outputs: list[dict[str, object]] = []
    identity_outputs: list[dict[str, object]] = []
    for output in outputs:
        if not isinstance(output, Mapping):
            raise BlenderRenderProvenanceError("render_provenance_output_invalid")
        artifact_type = output.get("artifact_type")
        digest = output.get("sha256")
        byte_length = output.get("byte_length")
        relative_path = output.get("relative_path")
        if (
            not isinstance(artifact_type, str)
            or not artifact_type
            or len(artifact_type) > 64
            or not _is_sha256(digest)
            or isinstance(byte_length, bool)
            or not isinstance(byte_length, int)
            or byte_length <= 0
            or not _safe_relative_path(relative_path)
        ):
            raise BlenderRenderProvenanceError("render_provenance_output_invalid")
        details = {
            key: value
            for key, value in output.items()
            if key not in {"artifact_type", "sha256", "byte_length", "relative_path"}
        }
        safe_details = _safe_json_mapping(details)
        item = {
            "artifact_type": artifact_type,
            "relative_path": relative_path,
            "sha256": digest,
            "byte_length": byte_length,
            **safe_details,
        }
        normalized_outputs.append(item)
        identity_outputs.append(
            {
                "artifact_type": artifact_type,
                "sha256": digest,
                "byte_length": byte_length,
                **safe_details,
            }
        )

    # Paths and timestamps are intentionally absent from this identity payload.
    identity_payload = {
        "contract": M14_RENDER_PROVENANCE_CONTRACT,
        "packlab": {"commit": packlab_commit, "version": packlab_version},
        "blender": {
            "executable_sha256": blender_executable_sha256,
            **normalized_build,
        },
        "scene_package": {
            "revision_id": scene_package_revision_id,
            "sha256": scene_package_sha256,
        },
        "source_revisions_and_digests": normalized_sources,
        "render": {
            "engine": render_engine,
            "device": render_device,
            "settings": normalized_settings,
            "camera_light_preset_ids": list(camera_light_preset_ids),
        },
        "outputs": identity_outputs,
        "limitations": _limitations(),
    }
    canonical = json.dumps(
        identity_payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    return {
        "contract": M14_RENDER_PROVENANCE_CONTRACT,
        "identity": "m14-render-provenance:" + digest,
        "identity_sha256": digest,
        "identity_payload": identity_payload,
        "outputs": normalized_outputs,
        "limitations": _limitations(),
    }


def _valid_blender_build(value: Mapping[str, object]) -> bool:
    version = value.get("version")
    if (
        not isinstance(version, (list, tuple))
        or len(version) != 3
        or any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in version)
    ):
        return False
    for key in ("version_string", "build_hash", "build_branch", "build_date"):
        field = value.get(key)
        if not isinstance(field, str) or not 0 < len(field) <= 128:
            return False
    return True


def _safe_json_mapping(value: Mapping[str, object]) -> dict[str, Any]:
    try:
        encoded = json.dumps(dict(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
        decoded = json.loads(encoded)
    except (TypeError, ValueError) as error:
        raise BlenderRenderProvenanceError("render_provenance_json_invalid") from error
    if not isinstance(decoded, dict) or _contains_ambient_path(decoded):
        raise BlenderRenderProvenanceError("render_provenance_ambient_path_forbidden")
    return decoded


def _contains_ambient_path(value: object) -> bool:
    if isinstance(value, dict):
        return any(_contains_ambient_path(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_ambient_path(item) for item in value)
    if isinstance(value, str):
        return (
            value.startswith(("/", "\\\\")) or re.match(r"^[A-Za-z]:[\\\\/].*", value) is not None
        )
    return False


def _safe_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        return False
    parts = value.split("/")
    return all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", part) for part in parts)


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _is_revision(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and len(value) <= 256
        and "/" not in value
        and "\\" not in value
    )


def _limitations() -> dict[str, object]:
    return {
        "derived_presentation_only": True,
        "cross_hardware_pixel_identity_guaranteed": False,
        "physical_accuracy_inferred": False,
        "physical_fit_verified": False,
        "material_certified": False,
        "manufacturing_approval_inferred": False,
        "regulatory_approval_inferred": False,
        "production_authority_escalated": False,
    }


__all__ = [
    "BlenderRenderProvenanceError",
    "M14_RENDER_PROVENANCE_CONTRACT",
    "create_m14_render_provenance",
]
