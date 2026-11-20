"""TLS and short-lived session authentication for PackLab Transfer V1."""

from __future__ import annotations

import hashlib
import ipaddress
import os
import secrets
import ssl
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .pairing import PairingOffer, PairingStore
from .transfer_protocol import REQUIRED_TRANSPORT, TransferErrorCode, TransferProtocolError


def certificate_fingerprint(certificate_path: str | Path) -> str:
    """Return the lowercase SHA-256 fingerprint of a PEM certificate's DER bytes."""

    path = Path(certificate_path)
    try:
        der = ssl.PEM_cert_to_DER_cert(path.read_text(encoding="ascii"))
    except (OSError, ValueError) as error:
        raise TransferProtocolError(
            TransferErrorCode.INTERNAL_ERROR, "TLS certificate is unavailable"
        ) from error
    return hashlib.sha256(der).hexdigest()


@dataclass(frozen=True, slots=True)
class TLSIdentity:
    certificate_path: Path
    private_key_path: Path
    fingerprint: str


def ensure_local_tls_identity(
    certificate_path: str | Path, private_key_path: str | Path, *, openssl: str = "openssl"
) -> TLSIdentity:
    """Create a local self-signed identity with OpenSSL when absent.

    The caller must provide a private, non-repository directory. The private
    key is never returned in a protocol message or diagnostic record.
    """

    certificate = Path(certificate_path)
    private_key = Path(private_key_path)
    if certificate.parent != private_key.parent:
        raise TransferProtocolError(
            TransferErrorCode.BAD_REQUEST, "certificate and key must share a private directory"
        )
    certificate.parent.mkdir(parents=True, exist_ok=True)
    if not certificate.exists() or not private_key.exists():
        try:
            subprocess.run(
                [
                    openssl,
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-keyout",
                    str(private_key),
                    "-out",
                    str(certificate),
                    "-days",
                    "2",
                    "-subj",
                    "/CN=PackLab Transfer Receiver",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            raise TransferProtocolError(
                TransferErrorCode.INTERNAL_ERROR, "local TLS identity could not be generated"
            ) from error
    try:
        os.chmod(private_key, 0o600)
    except OSError:
        pass
    return TLSIdentity(certificate, private_key, certificate_fingerprint(certificate))


def ensure_receiver_tls_identity(
    directory: str | Path,
    *,
    hosts: Sequence[str],
    validity: timedelta = timedelta(days=365),
    renew_before: timedelta = timedelta(days=7),
) -> TLSIdentity:
    """Create or reuse a self-signed receiver identity without an external tool.

    ``directory`` must be private and outside the repository. The identity is
    reused across runs (stable pin) and regenerated when it is near expiry,
    unreadable, or its subjectAltName does not cover every advertised host.
    The certificate follows Apple's TLS server rules (P-256, SHA-256, SAN,
    serverAuth EKU, validity under 398 days) so iOS accepts the pinned leaf.
    """

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

    root = Path(directory)
    certificate_path = root / "receiver.crt"
    private_key_path = root / "receiver.key"
    wanted: list[x509.GeneralName] = []
    for host in hosts:
        try:
            wanted.append(x509.IPAddress(ipaddress.ip_address(host)))
        except ValueError:
            wanted.append(x509.DNSName(host))
    now = datetime.now(UTC)
    try:
        existing = x509.load_pem_x509_certificate(certificate_path.read_bytes())
        key = serialization.load_pem_private_key(private_key_path.read_bytes(), password=None)
        san = existing.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        reusable = (
            existing.not_valid_before_utc <= now
            and existing.not_valid_after_utc - now > renew_before
            and all(name in san for name in wanted)
            and key.public_key().public_bytes(
                serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
            )
            == existing.public_key().public_bytes(
                serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )
    except (OSError, ValueError, TypeError, x509.ExtensionNotFound):
        reusable = False
    if not reusable:
        root.mkdir(parents=True, exist_ok=True)
        new_key = ec.generate_private_key(ec.SECP256R1())
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "PackLab Transfer Receiver")])
        certificate = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(new_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + validity)
            .add_extension(x509.SubjectAlternativeName(wanted), critical=False)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .sign(new_key, hashes.SHA256())
        )
        key_bytes = new_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        private_key_path.unlink(missing_ok=True)
        descriptor = os.open(private_key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(key_bytes)
        certificate_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    return TLSIdentity(
        certificate_path, private_key_path, certificate_fingerprint(certificate_path)
    )


def create_server_tls_context(identity: TLSIdentity) -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(certfile=identity.certificate_path, keyfile=identity.private_key_path)
    return context


@dataclass(frozen=True, slots=True)
class SessionCredential:
    receiver_instance_id: str
    token: str
    expires_at: float
    certificate_fingerprint: str


class PairingAuthenticator:
    def __init__(
        self,
        pairing_store: PairingStore,
        *,
        clock: Callable[[], float],
        session_ttl_seconds: int = 300,
    ) -> None:
        self._pairing_store = pairing_store
        self._clock = clock
        self._session_ttl = session_ttl_seconds
        self._sessions: dict[str, tuple[str, float, str, str]] = {}

    def authenticate_pairing(
        self,
        offer: PairingOffer,
        *,
        receiver_instance_id: str,
        pairing_code: str,
        certificate_fingerprint_value: str,
    ) -> SessionCredential:
        identity = self._pairing_store.pair(
            offer,
            receiver_instance_id=receiver_instance_id,
            pairing_code=pairing_code,
            tls_certificate_fingerprint=certificate_fingerprint_value,
        )
        token = secrets.token_urlsafe(32)
        expires_at = min(self._clock() + self._session_ttl, offer.expires_at + self._session_ttl)
        self._sessions[hashlib.sha256(token.encode("utf-8")).hexdigest()] = (
            identity.receiver_instance_id,
            expires_at,
            identity.tls_certificate_fingerprint,
            offer.pairing_id,
        )
        return SessionCredential(
            identity.receiver_instance_id, token, expires_at, identity.tls_certificate_fingerprint
        )

    def require_session(
        self,
        *,
        receiver_instance_id: str,
        token: str,
        certificate_fingerprint_value: str,
        transport: str = REQUIRED_TRANSPORT,
    ) -> None:
        if transport != REQUIRED_TRANSPORT:
            raise TransferProtocolError(TransferErrorCode.INSECURE_TRANSPORT, "HTTPS is required")
        record = self._sessions.get(hashlib.sha256(token.encode("utf-8")).hexdigest())
        if record is None:
            raise TransferProtocolError(TransferErrorCode.UNPAIRED, "session credential is unknown")
        expected_receiver, expires_at, expected_pin, _ = record
        if self._clock() >= expires_at:
            self._sessions.pop(hashlib.sha256(token.encode("utf-8")).hexdigest(), None)
            raise TransferProtocolError(
                TransferErrorCode.EXPIRED_PAIRING, "session credential has expired"
            )
        if receiver_instance_id != expected_receiver:
            raise TransferProtocolError(
                TransferErrorCode.WRONG_RECEIVER, "receiver identity does not match"
            )
        if certificate_fingerprint_value != expected_pin:
            raise TransferProtocolError(
                TransferErrorCode.WRONG_PIN, "certificate fingerprint does not match"
            )

    def revoke(self, credential: SessionCredential) -> None:
        self._sessions.pop(hashlib.sha256(credential.token.encode("utf-8")).hexdigest(), None)
