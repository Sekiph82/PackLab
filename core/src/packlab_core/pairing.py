"""Short-lived PackLab receiver pairing offers and minimum reconnect identity."""

from __future__ import annotations

import json
import secrets
import string
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass

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
