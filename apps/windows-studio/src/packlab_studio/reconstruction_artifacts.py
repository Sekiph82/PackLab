"""Local-only retention of reconstruction stage evidence.

The retainer preserves bytes and bounded process text without interpreting any
engine-specific output.  Evidence is immutable by stage/run identity and is
stored below the explicit revision-scoped reconstruction workspace.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from packlab_core.reconstruction import ReconstructionStageResult, StageStatus
from packlab_core.reconstruction_process import redact_portable_output

from .reconstruction_workspace import ReconstructionWorkspace

RECONSTRUCTION_EVIDENCE_CONTRACT = "packlab.reconstruction-stage-evidence.v1"
RECONSTRUCTION_EVIDENCE_CONTRACT_VERSION = "1"
MAX_RETAINED_LOG_CHARS = 16_384

_IDENTITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_PRIVATE_SEGMENTS = frozenset({"private", "supplier", "suppliers", "secret", "secrets", "kenya"})
_SOURCE_SEGMENTS = frozenset({"raw", "source", "source-evidence", "source_evidence", "raw_capture"})
_SECRET = re.compile(r"(?i)\b(?:token|password|secret|api[_-]?key|authorization)=\S+")
_BEARER = re.compile(r"(?i)\bBearer\s+\S+")


class ReconstructionEvidenceError(ValueError):
    """Base error for invalid, unsafe, or unavailable evidence."""


class ReconstructionEvidenceCollisionError(ReconstructionEvidenceError):
    """Raised when an evidence identity is already occupied by different data."""


class ReconstructionEvidenceRetentionError(ReconstructionEvidenceError):
    """Raised when an explicit output cannot be retained safely."""


@dataclass(frozen=True, slots=True)
class StageEvidenceRetentionRequest:
    """Complete caller-owned identity and evidence input for one stage run."""

    workspace: Path | ReconstructionWorkspace
    stage_id: str
    run_id: str
    stage_result: ReconstructionStageResult
    output_paths: Mapping[str, str | Path] | Sequence[str | Path]
    source_revision: str
    source_digest: str
    reconstruction_request_digest: str
    stage_digest: str
    output_identities: Mapping[str, str]
    provenance: Mapping[str, str] | None = None


@dataclass(frozen=True, slots=True)
class RetainedStageEvidence:
    """Stable result returned after new or idempotent evidence retention."""

    manifest_path: Path
    evidence_path: Path
    manifest: Mapping[str, object]
    idempotent: bool = False

    @property
    def retained_relative_paths(self) -> tuple[str, ...]:
        value = self.manifest.get("retained_relative_paths", ())
        return tuple(value) if isinstance(value, list) else ()

    @property
    def retention_failures(self) -> tuple[str, ...]:
        value = self.manifest.get("retention_failures", ())
        return tuple(value) if isinstance(value, list) else ()


def _identity(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _IDENTITY.fullmatch(value) is None:
        raise ReconstructionEvidenceError(f"{field_name} must be a safe identity")
    return value


def _digest(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise ReconstructionEvidenceError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _reject_casefold_duplicates(values: Sequence[str], field_name: str) -> None:
    seen: dict[str, str] = {}
    for value in values:
        folded = value.casefold()
        if folded in seen:
            raise ReconstructionEvidenceCollisionError(
                f"{field_name} collide under Windows case-insensitive semantics"
            )
        seen[folded] = value


def _safe_relative(value: str | Path, field_name: str) -> str:
    if isinstance(value, Path):
        if value.is_absolute() or value.drive or value.root:
            raise ReconstructionEvidenceError(f"{field_name} must be a safe relative path")
        text = value.as_posix()
    else:
        text = value
    if not isinstance(text, str):
        raise ReconstructionEvidenceError(f"{field_name} must be a safe relative path")
    if (
        not text
        or text.strip() != text
        or "\x00" in text
        or "\\" in text
        or text.startswith("/")
        or re.match(r"^[A-Za-z]:", text)
        or text.startswith("//")
    ):
        raise ReconstructionEvidenceError(f"{field_name} must be a safe relative path")
    parts = text.split("/")
    if any(not part or part in {".", ".."} for part in parts):
        raise ReconstructionEvidenceError(f"{field_name} contains traversal or empty components")
    lowered = {part.lower() for part in parts}
    if lowered & _PRIVATE_SEGMENTS:
        raise ReconstructionEvidenceError(f"{field_name} targets protected private data")
    if lowered & _SOURCE_SEGMENTS:
        raise ReconstructionEvidenceError(f"{field_name} targets source/raw evidence")
    if "evidence" in lowered:
        raise ReconstructionEvidenceError(f"{field_name} targets the retained evidence area")
    return PurePosixPath(*parts).as_posix()


def _redacted_bounded(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ReconstructionEvidenceError(f"{field_name} must be text")
    redacted = redact_portable_output(value)
    redacted = _SECRET.sub("[REDACTED_SECRET]", redacted)
    redacted = _BEARER.sub("[REDACTED_SECRET]", redacted)
    return redacted[:MAX_RETAINED_LOG_CHARS]


def _validate_stage_result(stage_id: str, result: object) -> ReconstructionStageResult:
    if not isinstance(result, ReconstructionStageResult):
        raise ReconstructionEvidenceError("stage_result must be a ReconstructionStageResult")
    if result.stage_id != stage_id:
        raise ReconstructionEvidenceError("stage result identity does not match stage_id")
    if not isinstance(result.status, StageStatus):
        raise ReconstructionEvidenceError("stage result status is invalid")
    if not isinstance(result.cancelled, bool):
        raise ReconstructionEvidenceError("stage result cancellation flag must be boolean")
    if isinstance(result.exit_code, bool) or not (
        result.exit_code is None or isinstance(result.exit_code, int)
    ):
        raise ReconstructionEvidenceError("stage result exit code is invalid")
    if isinstance(result.duration_seconds, bool) or not isinstance(
        result.duration_seconds, (int, float)
    ):
        raise ReconstructionEvidenceError("stage result duration is invalid")
    try:
        duration = float(result.duration_seconds)
    except (OverflowError, ValueError) as error:
        raise ReconstructionEvidenceError("stage result duration is invalid") from error
    if not math.isfinite(duration) or result.duration_seconds < 0:
        raise ReconstructionEvidenceError("stage result duration must be finite and non-negative")
    if result.status is StageStatus.SUCCEEDED:
        if result.cancelled or result.exit_code != 0:
            raise ReconstructionEvidenceError("successful stage result is incoherent")
    elif result.status is StageStatus.FAILED:
        if result.cancelled or result.exit_code == 0:
            raise ReconstructionEvidenceError("failed stage result is incoherent")
    elif result.status is StageStatus.CANCELLED:
        if not result.cancelled or result.exit_code == 0:
            raise ReconstructionEvidenceError("cancelled stage result is incoherent")
    _redacted_bounded(result.stdout, "stage_result.stdout")
    _redacted_bounded(result.stderr, "stage_result.stderr")
    if result.failure_reason is not None:
        _redacted_bounded(result.failure_reason, "stage_result.failure_reason")
    return result


def _workspace_path(value: Path | ReconstructionWorkspace) -> Path:
    path = value.path if isinstance(value, ReconstructionWorkspace) else Path(value)
    if not path.is_absolute():
        raise ReconstructionEvidenceError("workspace must be an explicit absolute path")
    if path.is_symlink() or not path.is_dir():
        raise ReconstructionEvidenceError("reconstruction workspace is missing or uses a symlink")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise ReconstructionEvidenceError("reconstruction workspace path uses a symlink")
    resolved = path.resolve(strict=True)
    return resolved


def _ensure_inside(root: Path, candidate: Path, field_name: str) -> Path:
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ReconstructionEvidenceError(
            f"{field_name} escapes the reconstruction workspace"
        ) from error
    return resolved


def _reject_symlink_components(root: Path, relative: str, field_name: str) -> Path:
    candidate = root.joinpath(*PurePosixPath(relative).parts)
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ReconstructionEvidenceError(f"{field_name} uses a symlink")
    return _ensure_inside(root, candidate, field_name)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_bytes(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}-", suffix=".tmp", dir=target.parent
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def _atomic_json(target: Path, value: object) -> None:
    _atomic_bytes(
        target,
        (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode(
            "utf-8"
        ),
    )


def _output_entries(
    workspace: Path,
    output_paths: Mapping[str, str | Path] | Sequence[str | Path],
    output_identities: Mapping[str, str],
) -> tuple[list[dict[str, object]], list[tuple[str, str, bytes]], list[str]]:
    if isinstance(output_paths, Mapping):
        if any(not isinstance(key, str) for key in output_paths):
            raise ReconstructionEvidenceError("output path keys must be text identities")
        supplied = dict(output_paths)
    elif isinstance(output_paths, Sequence) and not isinstance(
        output_paths, (str, bytes, bytearray)
    ):
        if any(not isinstance(value, (str, Path)) for value in output_paths):
            raise ReconstructionEvidenceError("output paths must be text or Path values")
        basenames = [Path(value).name for value in output_paths]
        _reject_casefold_duplicates(basenames, "sequence output basenames")
        supplied = dict(zip(basenames, output_paths, strict=True))
    else:
        raise ReconstructionEvidenceError("output_paths must be a mapping or sequence")
    if not supplied:
        raise ReconstructionEvidenceError("at least one explicit output path is required")
    _reject_casefold_duplicates(list(supplied), "output path identities")
    _reject_casefold_duplicates(list(output_identities), "output identity keys")
    if set(supplied) != set(output_identities):
        raise ReconstructionEvidenceError("output paths and output identities must have equal keys")

    entries: list[dict[str, object]] = []
    payloads: list[tuple[str, str, bytes]] = []
    failures: list[str] = []
    prepared: list[tuple[str, str, str, str, Path]] = []
    seen_sources: set[str] = set()
    seen_assets: set[str] = set()
    seen_retained: set[str] = set()
    for key in sorted(supplied):
        identity = _identity(key, "output identity key")
        asset_identity = _safe_relative(output_identities[key], "output identity")
        relative = _safe_relative(supplied[key], f"output path for {key}")
        source = _reject_symlink_components(workspace, relative, f"output path for {key}")
        source_key = relative.casefold()
        if source_key in seen_sources:
            raise ReconstructionEvidenceCollisionError(
                "two output identities target one source path under Windows semantics"
            )
        seen_sources.add(source_key)
        asset_key = asset_identity.casefold()
        if asset_key in seen_assets:
            raise ReconstructionEvidenceCollisionError(
                "two outputs use one output identity under Windows semantics"
            )
        seen_assets.add(asset_key)
        retained = f"outputs/{identity}{Path(relative).suffix}"
        retained_key = retained.casefold()
        if retained_key in seen_retained:
            raise ReconstructionEvidenceCollisionError(
                "two outputs target one retained path under Windows semantics"
            )
        seen_retained.add(retained_key)
        prepared.append((identity, asset_identity, relative, retained, source))

    for identity, asset_identity, relative, retained, source in prepared:
        try:
            if not source.is_file():
                raise OSError("output is not a regular file")
            data = source.read_bytes()
        except OSError as error:
            del error
            failures.append(f"{identity}:{relative}:missing_or_unreadable")
            continue
        entries.append(
            {
                "identity": identity,
                "output_identity": asset_identity,
                "source_relative_path": relative,
                "retained_relative_path": retained,
                "byte_size": len(data),
                "sha256": _sha256(data),
            }
        )
        payloads.append((retained, identity, data))
    return entries, payloads, failures


class ReconstructionEvidenceRetainer:
    """Retain immutable stage evidence below one explicit workspace."""

    def retain(self, request: StageEvidenceRetentionRequest) -> RetainedStageEvidence:
        if not isinstance(request, StageEvidenceRetentionRequest):
            raise ReconstructionEvidenceError("request must be StageEvidenceRetentionRequest")
        workspace = _workspace_path(request.workspace)
        stage_id = _identity(request.stage_id, "stage_id")
        run_id = _identity(request.run_id, "run_id")
        result = _validate_stage_result(stage_id, request.stage_result)
        source_revision = _identity(request.source_revision, "source_revision")
        source_digest = _digest(request.source_digest, "source_digest")
        request_digest = _digest(
            request.reconstruction_request_digest, "reconstruction_request_digest"
        )
        stage_digest = _digest(request.stage_digest, "stage_digest")
        if not isinstance(request.output_identities, Mapping):
            raise ReconstructionEvidenceError("output_identities must be a mapping")
        if any(not isinstance(key, str) for key in request.output_identities):
            raise ReconstructionEvidenceError("output identity keys must be text identities")
        output_identities = dict(request.output_identities)
        for value in output_identities.values():
            if not isinstance(value, str):
                raise ReconstructionEvidenceError("output identities must be text")
        if request.provenance is not None and not isinstance(request.provenance, Mapping):
            raise ReconstructionEvidenceError("provenance must be a mapping")
        provenance = {} if request.provenance is None else dict(request.provenance)
        if any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in provenance.items()
        ):
            raise ReconstructionEvidenceError("provenance links must be text")
        for key, value in provenance.items():
            _identity(key, "provenance key")
            if _CONTROL.search(value):
                raise ReconstructionEvidenceError("provenance links contain control characters")
        if set(provenance) & {
            "reconstruction_request_digest",
            "stage_digest",
            "output_identities",
        }:
            raise ReconstructionEvidenceError("provenance cannot override canonical identity links")

        output_entries, payloads, retention_failures = _output_entries(
            workspace, request.output_paths, output_identities
        )
        stdout = _redacted_bounded(result.stdout, "stage_result.stdout")
        stderr = _redacted_bounded(result.stderr, "stage_result.stderr")
        failure_reason = (
            None
            if result.failure_reason is None
            else _redacted_bounded(result.failure_reason, "stage_result.failure_reason")
        )
        logs = {
            "stdout": {
                "retained_relative_path": "logs/stdout.txt",
                "byte_size": len(stdout.encode("utf-8")),
                "sha256": _sha256(stdout.encode("utf-8")),
            },
            "stderr": {
                "retained_relative_path": "logs/stderr.txt",
                "byte_size": len(stderr.encode("utf-8")),
                "sha256": _sha256(stderr.encode("utf-8")),
            },
        }
        manifest: dict[str, object] = {
            "contract": RECONSTRUCTION_EVIDENCE_CONTRACT,
            "contract_version": RECONSTRUCTION_EVIDENCE_CONTRACT_VERSION,
            "stage_id": stage_id,
            "run_id": run_id,
            "source_revision": source_revision,
            "source_digest": source_digest,
            "stage_status": result.status.value,
            "status": result.status.value,
            "exit_code": result.exit_code,
            "duration_seconds": float(result.duration_seconds),
            "cancelled": result.cancelled,
            "failure_reason": failure_reason,
            "stdout": stdout,
            "stderr": stderr,
            "logs": logs,
            "outputs": output_entries,
            "retained_relative_paths": [
                "logs/stderr.txt",
                "logs/stdout.txt",
                *(entry["retained_relative_path"] for entry in output_entries),
            ],
            "provenance": {
                "reconstruction_request_digest": request_digest,
                "stage_digest": stage_digest,
                "output_identities": {
                    key: output_identities[key] for key in sorted(output_identities)
                },
                **{key: provenance[key] for key in sorted(provenance)},
            },
            "retention_failures": retention_failures,
            "retention_status": "bounded_failure" if retention_failures else "retained",
            "regeneration": {"local_only": True, "source_revision": source_revision},
        }
        evidence_path = self._ensure_evidence_parent(workspace, stage_id, run_id)
        if evidence_path.is_symlink():
            raise ReconstructionEvidenceError("stage/run evidence identity uses a symlink")
        if evidence_path.exists():
            return self._resolve_existing(evidence_path, manifest)

        staging = Path(tempfile.mkdtemp(prefix=".stage-evidence-", dir=workspace))
        created_evidence = False
        try:
            for retained, _, data in payloads:
                _atomic_bytes(staging / retained, data)
            _atomic_bytes(staging / "logs" / "stdout.txt", stdout.encode("utf-8"))
            _atomic_bytes(staging / "logs" / "stderr.txt", stderr.encode("utf-8"))
            _atomic_json(staging / "manifest.json", manifest)
            try:
                evidence_path.mkdir(parents=False)
            except FileExistsError as error:
                raise ReconstructionEvidenceCollisionError(
                    "stage/run evidence identity appeared during retention"
                ) from error
            created_evidence = True
            for child in staging.iterdir():
                os.replace(child, evidence_path / child.name)
            staging.rmdir()
        except Exception:
            if created_evidence:
                shutil.rmtree(evidence_path, ignore_errors=True)
            shutil.rmtree(staging, ignore_errors=True)
            raise
        return RetainedStageEvidence(
            evidence_path / "manifest.json", evidence_path, manifest, idempotent=False
        )

    def _ensure_evidence_parent(self, workspace: Path, stage_id: str, run_id: str) -> Path:
        evidence_root = workspace / "evidence"
        if evidence_root.exists() and evidence_root.is_symlink():
            raise ReconstructionEvidenceError("evidence root uses a symlink")
        if evidence_root.exists() and not evidence_root.is_dir():
            raise ReconstructionEvidenceError("evidence root is not a directory")
        try:
            evidence_root.mkdir(exist_ok=True)
        except OSError as error:
            raise ReconstructionEvidenceError("evidence root cannot be created") from error

        stage_path = self._casefold_existing_child(
            evidence_root, stage_id, "stage evidence identity"
        )
        if stage_path is None:
            stage_path = evidence_root / stage_id
            try:
                stage_path.mkdir()
            except FileExistsError as error:
                raise ReconstructionEvidenceCollisionError(
                    "stage evidence identity appeared during retention"
                ) from error
            except OSError as error:
                raise ReconstructionEvidenceError(
                    "stage evidence directory cannot be created"
                ) from error
        if stage_path.is_symlink():
            raise ReconstructionEvidenceError("stage evidence directory uses a symlink")
        if not stage_path.is_dir():
            raise ReconstructionEvidenceCollisionError("stage evidence identity is not a directory")

        run_path = self._casefold_existing_child(stage_path, run_id, "stage/run evidence identity")
        if run_path is None:
            return stage_path / run_id
        if run_path.is_symlink():
            raise ReconstructionEvidenceError("stage/run evidence identity uses a symlink")
        return run_path

    @staticmethod
    def _casefold_existing_child(parent: Path, name: str, field_name: str) -> Path | None:
        try:
            matches = [
                child for child in parent.iterdir() if child.name.casefold() == name.casefold()
            ]
        except OSError as error:
            raise ReconstructionEvidenceError(f"{field_name} cannot be inspected") from error
        if len(matches) > 1 or (matches and matches[0].name != name):
            raise ReconstructionEvidenceCollisionError(
                f"{field_name} collides under Windows case-insensitive semantics"
            )
        return matches[0] if matches else None

    def _resolve_existing(
        self, evidence_path: Path, expected: Mapping[str, object]
    ) -> RetainedStageEvidence:
        manifest_path = evidence_path / "manifest.json"
        try:
            actual = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ReconstructionEvidenceCollisionError(
                "stage/run evidence identity has no valid manifest"
            ) from error
        if actual != dict(expected):
            raise ReconstructionEvidenceCollisionError(
                "same stage/run identity has different bytes or provenance"
            )
        retained_paths = expected.get("retained_relative_paths")
        if not isinstance(retained_paths, list) or not all(
            isinstance(relative, str) for relative in retained_paths
        ):
            raise ReconstructionEvidenceCollisionError("retained paths metadata is invalid")
        _reject_casefold_duplicates(retained_paths, "retained paths")

        records: dict[str, Mapping[str, object]] = {}

        def add_record(record: object) -> None:
            if not isinstance(record, Mapping):
                raise ReconstructionEvidenceCollisionError("retained evidence metadata is invalid")
            relative = record.get("retained_relative_path")
            if not isinstance(relative, str):
                raise ReconstructionEvidenceCollisionError(
                    "retained evidence path metadata is invalid"
                )
            try:
                normalized = _safe_relative(relative, "retained evidence path")
            except ReconstructionEvidenceError as error:
                raise ReconstructionEvidenceCollisionError(
                    "retained evidence path metadata is unsafe"
                ) from error
            if normalized != relative or normalized in records:
                raise ReconstructionEvidenceCollisionError(
                    "retained evidence paths are inconsistent"
                )
            records[normalized] = record

        logs = expected.get("logs")
        if not isinstance(logs, Mapping):
            raise ReconstructionEvidenceCollisionError("retained log metadata is invalid")
        for record in logs.values():
            add_record(record)
        outputs = expected.get("outputs")
        if not isinstance(outputs, list):
            raise ReconstructionEvidenceCollisionError("retained output metadata is invalid")
        for record in outputs:
            add_record(record)
        if set(records) != set(retained_paths):
            raise ReconstructionEvidenceCollisionError("retained evidence paths are inconsistent")

        for relative, record in records.items():
            try:
                path = _reject_symlink_components(evidence_path, relative, "retained evidence path")
            except ReconstructionEvidenceError as error:
                raise ReconstructionEvidenceCollisionError(
                    "retained evidence path was altered"
                ) from error
            if path.is_symlink() or not path.is_file():
                raise ReconstructionEvidenceCollisionError("retained evidence was altered")
            byte_size = record.get("byte_size")
            digest = record.get("sha256")
            if isinstance(byte_size, bool) or not isinstance(byte_size, int) or byte_size < 0:
                raise ReconstructionEvidenceCollisionError("retained byte-size metadata is invalid")
            if not isinstance(digest, str) or _DIGEST.fullmatch(digest) is None:
                raise ReconstructionEvidenceCollisionError("retained digest metadata is invalid")
            try:
                data = path.read_bytes()
            except OSError as error:
                raise ReconstructionEvidenceCollisionError(
                    "retained evidence was altered"
                ) from error
            if len(data) != byte_size or _sha256(data) != digest:
                raise ReconstructionEvidenceCollisionError("retained evidence bytes were altered")

        actual_files: set[str] = set()
        for path in evidence_path.rglob("*"):
            if path.is_symlink():
                raise ReconstructionEvidenceCollisionError("retained evidence uses a symlink")
            if path.is_file() and path.name != "manifest.json":
                actual_files.add(path.relative_to(evidence_path).as_posix())
        if actual_files != set(retained_paths):
            raise ReconstructionEvidenceCollisionError("retained evidence file set was altered")
        return RetainedStageEvidence(manifest_path, evidence_path, actual, idempotent=True)


def retain_reconstruction_stage_evidence(
    workspace: Path | ReconstructionWorkspace,
    stage_id: str,
    run_id: str,
    stage_result: ReconstructionStageResult,
    output_paths: Mapping[str, str | Path] | Sequence[str | Path],
    *,
    source_revision: str,
    source_digest: str,
    reconstruction_request_digest: str,
    stage_digest: str,
    output_identities: Mapping[str, str],
    provenance: Mapping[str, str] | None = None,
) -> RetainedStageEvidence:
    """Retain one stage's explicit outputs and bounded logs."""

    request = StageEvidenceRetentionRequest(
        workspace,
        stage_id,
        run_id,
        stage_result,
        output_paths,
        source_revision,
        source_digest,
        reconstruction_request_digest,
        stage_digest,
        output_identities,
        provenance,
    )
    return ReconstructionEvidenceRetainer().retain(request)


retain_stage_evidence = retain_reconstruction_stage_evidence
ReconstructionStageEvidenceRetainer = ReconstructionEvidenceRetainer
ReconstructionStageEvidenceRequest = StageEvidenceRetentionRequest


__all__ = [
    "MAX_RETAINED_LOG_CHARS",
    "RECONSTRUCTION_EVIDENCE_CONTRACT",
    "RECONSTRUCTION_EVIDENCE_CONTRACT_VERSION",
    "ReconstructionEvidenceCollisionError",
    "ReconstructionEvidenceError",
    "ReconstructionEvidenceRetentionError",
    "ReconstructionEvidenceRetainer",
    "ReconstructionStageEvidenceRetainer",
    "ReconstructionStageEvidenceRequest",
    "RetainedStageEvidence",
    "StageEvidenceRetentionRequest",
    "retain_reconstruction_stage_evidence",
    "retain_stage_evidence",
]
