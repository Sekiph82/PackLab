"""PackLab Transfer Protocol V1 wire contracts.

The protocol describes an opaque finalized `.packscan` byte stream. It does
not expose mutable session files or define a second package format.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

PROTOCOL_NAME = "packlab-transfer"
PROTOCOL_VERSION = "1"
REQUIRED_TRANSPORT = "https"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class TransferProtocolError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class TransferErrorCode(StrEnum):
    BAD_REQUEST = "bad_request"
    UNSUPPORTED_VERSION = "unsupported_version"
    INSECURE_TRANSPORT = "insecure_transport"
    UNPAIRED = "unpaired"
    WRONG_RECEIVER = "wrong_receiver"
    WRONG_PIN = "wrong_pin"
    EXPIRED_PAIRING = "expired_pairing"
    REPLAYED_PAIRING = "replayed_pairing"
    UNKNOWN_TRANSFER = "unknown_transfer"
    CONFLICTING_CHUNK = "conflicting_chunk"
    OUT_OF_ORDER = "out_of_order"
    CHECKSUM_MISMATCH = "checksum_mismatch"
    CANCELLED = "cancelled"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True, slots=True)
class TransferErrorEnvelope:
    """Stable error wire response; diagnostics never contain credentials or paths."""

    code: str
    message: str
    protocol_version: str = PROTOCOL_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "message": "error",
            "protocol": PROTOCOL_NAME,
            "protocol_version": self.protocol_version,
            "error_code": self.code,
            "error": self.message,
        }


def _require_string(value: Any, field: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value):
        raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, f"{field} must be a string")
    return value


def _require_sha256(value: Any, field: str) -> str:
    text = _require_string(value, field)
    if not SHA256_RE.fullmatch(text):
        raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, f"{field} must be lowercase SHA-256")
    return text


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


@dataclass(frozen=True, slots=True)
class TransferCreate:
    receiver_id: str
    transfer_id: str
    capture_id: str
    package_name: str
    total_bytes: int
    package_sha256: str
    protocol_version: str = PROTOCOL_VERSION
    transport: str = REQUIRED_TRANSPORT

    def __post_init__(self) -> None:
        for field in ("receiver_id", "transfer_id", "capture_id", "package_name"):
            _require_string(getattr(self, field), field)
        if self.protocol_version != PROTOCOL_VERSION:
            raise TransferProtocolError(TransferErrorCode.UNSUPPORTED_VERSION, "protocol version is not supported")
        if self.transport != REQUIRED_TRANSPORT:
            raise TransferProtocolError(TransferErrorCode.INSECURE_TRANSPORT, "production transport must be HTTPS")
        if self.total_bytes < 0:
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "total_bytes must be non-negative")
        _require_sha256(self.package_sha256, "package_sha256")
        if not self.package_name.lower().endswith(".packscan"):
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "package_name must be a .packscan")

    def to_dict(self) -> dict[str, object]:
        return {
            "message": "create_transfer",
            "protocol": PROTOCOL_NAME,
            "protocol_version": self.protocol_version,
            "transport": self.transport,
            "receiver_id": self.receiver_id,
            "transfer_id": self.transfer_id,
            "capture_id": self.capture_id,
            "package_name": self.package_name,
            "total_bytes": self.total_bytes,
            "package_sha256": self.package_sha256,
        }

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> TransferCreate:
        if value.get("message") != "create_transfer" or value.get("protocol") != PROTOCOL_NAME:
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "not a create_transfer message")
        try:
            return cls(
                receiver_id=_require_string(value.get("receiver_id"), "receiver_id"),
                transfer_id=_require_string(value.get("transfer_id"), "transfer_id"),
                capture_id=_require_string(value.get("capture_id"), "capture_id"),
                package_name=_require_string(value.get("package_name"), "package_name"),
                total_bytes=int(value.get("total_bytes", -1)),
                package_sha256=_require_sha256(value.get("package_sha256"), "package_sha256"),
                protocol_version=_require_string(value.get("protocol_version"), "protocol_version"),
                transport=_require_string(value.get("transport"), "transport"),
            )
        except (TypeError, ValueError) as error:
            if isinstance(error, TransferProtocolError):
                raise
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "create_transfer fields are invalid") from error


@dataclass(frozen=True, slots=True)
class TransferStatus:
    transfer_id: str
    confirmed_bytes: int
    total_bytes: int
    state: str
    package_sha256: str
    next_offset: int
    protocol_version: str = PROTOCOL_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "message": "transfer_status",
            "protocol": PROTOCOL_NAME,
            "protocol_version": self.protocol_version,
            "transfer_id": self.transfer_id,
            "confirmed_bytes": self.confirmed_bytes,
            "total_bytes": self.total_bytes,
            "state": self.state,
            "package_sha256": self.package_sha256,
            "next_offset": self.next_offset,
        }

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> TransferStatus:
        if value.get("message") != "transfer_status" or value.get("protocol") != PROTOCOL_NAME:
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "not a transfer_status message")
        if value.get("protocol_version") != PROTOCOL_VERSION:
            raise TransferProtocolError(TransferErrorCode.UNSUPPORTED_VERSION, "protocol version is not supported")
        try:
            return cls(
                transfer_id=_require_string(value.get("transfer_id"), "transfer_id"),
                confirmed_bytes=int(value["confirmed_bytes"]),
                total_bytes=int(value["total_bytes"]),
                state=_require_string(value.get("state"), "state"),
                package_sha256=_require_sha256(value.get("package_sha256"), "package_sha256"),
                next_offset=int(value["next_offset"]),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "transfer_status fields are invalid") from error


@dataclass(frozen=True, slots=True)
class TransferControlMessage:
    transfer_id: str
    action: str
    protocol_version: str = PROTOCOL_VERSION

    def __post_init__(self) -> None:
        _require_string(self.transfer_id, "transfer_id")
        if self.action not in {"cancel", "resume"}:
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "unsupported transfer control action")

    def to_dict(self) -> dict[str, object]:
        return {
            "message": self.action,
            "protocol": PROTOCOL_NAME,
            "protocol_version": self.protocol_version,
            "transfer_id": self.transfer_id,
        }


@dataclass(frozen=True, slots=True)
class ChunkRange:
    transfer_id: str
    offset: int
    length: int
    chunk_sha256: str

    def __post_init__(self) -> None:
        _require_string(self.transfer_id, "transfer_id")
        if self.offset < 0 or self.length <= 0:
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "chunk range is invalid")
        _require_sha256(self.chunk_sha256, "chunk_sha256")

    def validate_bytes(self, payload: bytes) -> None:
        if len(payload) != self.length:
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "chunk length does not match body")
        if hashlib.sha256(payload).hexdigest() != self.chunk_sha256:
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "chunk digest does not match body")

    def to_dict(self) -> dict[str, object]:
        return {
            "message": "put_chunk",
            "protocol": PROTOCOL_NAME,
            "protocol_version": PROTOCOL_VERSION,
            "transfer_id": self.transfer_id,
            "offset": self.offset,
            "length": self.length,
            "chunk_sha256": self.chunk_sha256,
        }


@dataclass(frozen=True, slots=True)
class CompletionAcknowledgement:
    transfer_id: str
    package_sha256: str
    verified: bool
    authenticated: bool
    state: str

    def to_dict(self) -> dict[str, object]:
        return {
            "message": "completion_acknowledgement",
            "protocol": PROTOCOL_NAME,
            "protocol_version": PROTOCOL_VERSION,
            "transfer_id": self.transfer_id,
            "package_sha256": self.package_sha256,
            "verified": self.verified,
            "authenticated": self.authenticated,
            "state": self.state,
        }

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> CompletionAcknowledgement:
        if value.get("message") != "completion_acknowledgement" or value.get("protocol") != PROTOCOL_NAME:
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "not a completion acknowledgement")
        if value.get("protocol_version") != PROTOCOL_VERSION:
            raise TransferProtocolError(TransferErrorCode.UNSUPPORTED_VERSION, "protocol version is not supported")
        if not isinstance(value.get("verified"), bool) or not isinstance(value.get("authenticated"), bool):
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "completion acknowledgement flags are invalid")
        return cls(
            transfer_id=_require_string(value.get("transfer_id"), "transfer_id"),
            package_sha256=_require_sha256(value.get("package_sha256"), "package_sha256"),
            verified=value["verified"], authenticated=value["authenticated"], state=_require_string(value.get("state"), "state"),
        )
