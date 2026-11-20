"""PackLab receiver pairing: one-time offers and long-lived, revocable device credentials."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import string
import tempfile
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .transfer_protocol import (
    PROTOCOL_NAME,
    PROTOCOL_VERSION,
    TransferErrorCode,
    TransferProtocolError,
    canonical_json,
)

_CODE_ALPHABET = string.ascii_uppercase + string.digits


@dataclass(frozen=True, slots=True)
class PairingOffer:
    receiver_instance_id: str
    host: str
    port: int
    pairing_id: str
    pairing_code: str
    expires_at: float
    tls_certificate_fingerprint: str
    protocol_version: str = PROTOCOL_VERSION

    def public_dict(self) -> dict[str, object]:
        return {
            "protocol": PROTOCOL_NAME,
            "protocol_version": self.protocol_version,
            "receiver_instance_id": self.receiver_instance_id,
            "host": self.host,
            "port": self.port,
            "pairing_id": self.pairing_id,
            "pairing_code": self.pairing_code,
            "expires_at": self.expires_at,
            "tls_certificate_fingerprint": self.tls_certificate_fingerprint,
        }

    def qr_payload(self) -> str:
        return canonical_json(self.public_dict()).decode("utf-8").rstrip("\n")

    @classmethod
    def from_qr_payload(cls, payload: str) -> PairingOffer:
        try:
            value = json.loads(payload)
        except json.JSONDecodeError as error:
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "pairing QR payload is malformed") from error
        if not isinstance(value, dict):
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "pairing QR payload must be an object")
        required = ("receiver_instance_id", "host", "pairing_id", "pairing_code", "tls_certificate_fingerprint")
        if value.get("protocol") != PROTOCOL_NAME or value.get("protocol_version") != PROTOCOL_VERSION:
            raise TransferProtocolError(TransferErrorCode.UNSUPPORTED_VERSION, "pairing protocol is not supported")
        if any(not isinstance(value.get(key), str) or not value[key] for key in required):
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "pairing identity is incomplete")
        if not isinstance(value.get("port"), int) or not 1 <= value["port"] <= 65535:
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "pairing port is invalid")
        if not isinstance(value.get("expires_at"), int | float):
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "pairing expiry is invalid")
        return cls(
            receiver_instance_id=value["receiver_instance_id"], host=value["host"], port=value["port"],
            pairing_id=value["pairing_id"], pairing_code=value["pairing_code"], expires_at=float(value["expires_at"]),
            tls_certificate_fingerprint=value["tls_certificate_fingerprint"],
        )


@dataclass(frozen=True, slots=True)
class PairedReceiverIdentity:
    receiver_instance_id: str
    host: str
    port: int
    tls_certificate_fingerprint: str


class PairingStore:
    """In-memory one-time offer store; only non-secret identity is exportable."""

    def __init__(self, *, clock: Callable[[], float] = time.time) -> None:
        self._clock = clock
        self._offers: dict[str, PairingOffer] = {}
        self._used: set[str] = set()
        self._paired: dict[str, PairedReceiverIdentity] = {}

    def create_offer(self, *, receiver_instance_id: str, host: str, port: int, tls_certificate_fingerprint: str, ttl_seconds: int = 120) -> PairingOffer:
        if ttl_seconds <= 0 or ttl_seconds > 900:
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "pairing TTL is outside the short-lived range")
        offer = PairingOffer(
            receiver_instance_id=receiver_instance_id, host=host, port=port,
            pairing_id=uuid.uuid4().hex, pairing_code="".join(secrets.choice(_CODE_ALPHABET) for _ in range(8)),
            expires_at=self._clock() + ttl_seconds, tls_certificate_fingerprint=tls_certificate_fingerprint,
        )
        self._offers[offer.pairing_id] = offer
        return offer

    def pair(self, offer: PairingOffer, *, receiver_instance_id: str, pairing_code: str, tls_certificate_fingerprint: str) -> PairedReceiverIdentity:
        current = self._offers.get(offer.pairing_id)
        if current is None or offer.pairing_id in self._used:
            raise TransferProtocolError(TransferErrorCode.REPLAYED_PAIRING, "pairing offer was already used")
        if self._clock() >= current.expires_at:
            raise TransferProtocolError(TransferErrorCode.EXPIRED_PAIRING, "pairing offer has expired")
        if receiver_instance_id != current.receiver_instance_id or offer.receiver_instance_id != current.receiver_instance_id:
            raise TransferProtocolError(TransferErrorCode.WRONG_RECEIVER, "receiver identity does not match offer")
        if pairing_code.replace("-", "").upper() != current.pairing_code:
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "pairing code is invalid")
        if tls_certificate_fingerprint != current.tls_certificate_fingerprint:
            raise TransferProtocolError(TransferErrorCode.WRONG_PIN, "receiver certificate fingerprint does not match")
        identity = PairedReceiverIdentity(current.receiver_instance_id, current.host, current.port, current.tls_certificate_fingerprint)
        self._used.add(current.pairing_id)
        self._offers.pop(current.pairing_id, None)
        self._paired[identity.receiver_instance_id] = identity
        return identity

    def paired_identity(self, receiver_instance_id: str) -> PairedReceiverIdentity | None:
        return self._paired.get(receiver_instance_id)

    def revoke(self, pairing_id: str) -> None:
        self._offers.pop(pairing_id, None)
        self._used.add(pairing_id)


#: Device-session requests must carry a timestamp within this many seconds of
#: the receiver clock; their nonce is remembered for twice this window.
DEVICE_REQUEST_SKEW_SECONDS = 300


@dataclass(frozen=True, slots=True)
class PairedDevice:
    """A phone that completed one-time pairing. Only the secret's SHA-256 is kept."""

    device_id: str
    device_name: str
    secret_sha256: str
    paired_at: float
    last_seen_at: float | None = None
    revoked_at: float | None = None

    @property
    def active(self) -> bool:
        return self.revoked_at is None


class DeviceRegistry:
    """Long-lived paired-device credentials, persisted outside the repository.

    Pairing once (one-time offer + code) registers a device and returns its
    secret exactly once. Later connections present ``device_id`` + secret over
    the pinned TLS channel together with a fresh nonce and timestamp; the
    registry stores only ``sha256(secret)``, rejects stale timestamps and
    reused nonces, and a revoked device can never open a session again.
    ``path=None`` keeps the registry in memory (tests, ephemeral receivers).
    """

    def __init__(self, path: str | Path | None = None, *, clock: Callable[[], float] = time.time) -> None:
        self._path = Path(path) if path is not None else None
        self._clock = clock
        self._lock = threading.Lock()
        self._devices: dict[str, PairedDevice] = {}
        self._nonces: dict[str, float] = {}
        if self._path is not None and self._path.is_file():
            try:
                stored = json.loads(self._path.read_text(encoding="utf-8"))
                devices = stored["devices"] if stored.get("version") == 1 else []
                self._devices = {item["device_id"]: PairedDevice(**item) for item in devices}
            except (OSError, ValueError, TypeError, KeyError) as error:
                # Fail closed: an unreadable registry must not silently drop revocations.
                raise TransferProtocolError(TransferErrorCode.INTERNAL_ERROR, "paired-device registry is unreadable") from error

    def register(self, device_name: str) -> tuple[PairedDevice, str]:
        name = (device_name.strip() or "iPhone")[:64]
        secret = secrets.token_urlsafe(32)
        device = PairedDevice(uuid.uuid4().hex, name, _secret_digest(secret), self._clock())
        with self._lock:
            self._devices[device.device_id] = device
            self._persist()
        return device, secret

    def authenticate(self, device_id: str, device_secret: str, *, nonce: str, timestamp: float) -> PairedDevice:
        now = self._clock()
        with self._lock:
            device = self._devices.get(device_id)
            # Unknown id and wrong secret are indistinguishable to the caller.
            if device is None or not hmac.compare_digest(device.secret_sha256, _secret_digest(device_secret)):
                raise TransferProtocolError(TransferErrorCode.UNPAIRED, "device credential is unknown")
            if not device.active:
                raise TransferProtocolError(TransferErrorCode.DEVICE_REVOKED, "this device was unpaired in PackLab Studio")
            if not 16 <= len(nonce) <= 128 or abs(now - timestamp) > DEVICE_REQUEST_SKEW_SECONDS:
                raise TransferProtocolError(TransferErrorCode.REPLAYED_REQUEST, "device request is stale or malformed")
            self._nonces = {key: expiry for key, expiry in self._nonces.items() if expiry > now}
            key = f"{device_id}:{nonce}"
            if key in self._nonces:
                raise TransferProtocolError(TransferErrorCode.REPLAYED_REQUEST, "device request was already used")
            self._nonces[key] = now + 2 * DEVICE_REQUEST_SKEW_SECONDS
            device = replace(device, last_seen_at=now)
            self._devices[device_id] = device
            self._persist()
            return device

    def is_active(self, device_id: str) -> bool:
        device = self._devices.get(device_id)
        return device is not None and device.active

    def revoke(self, device_id: str) -> bool:
        with self._lock:
            device = self._devices.get(device_id)
            if device is None or not device.active:
                return False
            self._devices[device_id] = replace(device, revoked_at=self._clock())
            self._persist()
            return True

    def devices(self) -> list[PairedDevice]:
        return sorted(self._devices.values(), key=lambda device: device.paired_at)

    def _persist(self) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        body = json.dumps({"version": 1, "devices": [asdict(device) for device in self.devices()]}, indent=2, sort_keys=True)
        descriptor, temporary = tempfile.mkstemp(dir=self._path.parent, prefix=".paired-devices-")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(body)
            try:
                os.chmod(temporary, 0o600)
            except OSError:
                pass
            os.replace(temporary, self._path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise


def _secret_digest(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()
