"""Ephemeral non-production TLS material for executable loopback tests."""

from __future__ import annotations

import ipaddress
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from packlab_core.transfer_security import TLSIdentity, certificate_fingerprint


def create_test_tls_identity(root: Path, *, common_name: str = "127.0.0.1") -> TLSIdentity:
    """Create an ephemeral self-signed certificate without an external tool.

    The key is written only below pytest's temporary directory and is never a
    repository fixture or a production identity.
    """

    root.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(minutes=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(common_name))]), critical=False)
        .sign(key, hashes.SHA256())
    )
    certificate_path = root / "receiver.crt"
    private_key_path = root / "receiver.key"
    certificate_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    private_key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
    return TLSIdentity(certificate_path, private_key_path, certificate_fingerprint(certificate_path))
