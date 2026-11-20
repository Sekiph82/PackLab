from __future__ import annotations

import hashlib
import ipaddress
import socket
import ssl
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import ExtendedKeyUsageOID

from packlab_core.transfer_security import certificate_fingerprint, ensure_receiver_tls_identity
from packlab_studio.receiver_session import ReceiverSession, detect_lan_ipv4


def _no_openssl(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("production TLS identity must not shell out")


def test_identity_is_created_without_openssl_and_is_ios_compatible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(subprocess, "run", _no_openssl)
    identity = ensure_receiver_tls_identity(tmp_path / "tls", hosts=["192.168.1.20", "127.0.0.1"])
    cert = x509.load_pem_x509_certificate(identity.certificate_path.read_bytes())
    san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    assert ipaddress.ip_address("192.168.1.20") in san.get_values_for_type(x509.IPAddress)
    eku = cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
    assert ExtendedKeyUsageOID.SERVER_AUTH in eku
    assert cert.not_valid_after_utc - cert.not_valid_before_utc < timedelta(days=398)
    # iOS pins lowercase hex SHA-256 of the leaf DER (TransferTLS.swift).
    expected = cert.fingerprint(hashes.SHA256()).hex()
    assert identity.fingerprint == expected == certificate_fingerprint(identity.certificate_path)
    assert "PRIVATE KEY" in identity.private_key_path.read_text("ascii")


def test_identity_is_reused_and_regenerated_for_new_host_or_expiry(tmp_path: Path) -> None:
    first = ensure_receiver_tls_identity(tmp_path, hosts=["10.0.0.5"])
    assert (
        ensure_receiver_tls_identity(tmp_path, hosts=["10.0.0.5"]).fingerprint == first.fingerprint
    )
    moved = ensure_receiver_tls_identity(tmp_path, hosts=["10.0.0.9"])
    assert moved.fingerprint != first.fingerprint
    short = tmp_path / "short"
    near_expiry = ensure_receiver_tls_identity(
        short, hosts=["10.0.0.9"], validity=timedelta(days=1)
    )
    cert = x509.load_pem_x509_certificate(near_expiry.certificate_path.read_bytes())
    assert cert.not_valid_after_utc < datetime.now(UTC) + timedelta(days=2)
    renewed = ensure_receiver_tls_identity(short, hosts=["10.0.0.9"])
    assert renewed.fingerprint != near_expiry.fingerprint
    near_expiry.private_key_path.write_text("corrupt", encoding="ascii")
    assert ensure_receiver_tls_identity(tmp_path, hosts=["10.0.0.9"]).fingerprint


def test_served_leaf_matches_offer_pin_like_ios(tmp_path: Path) -> None:
    session = ReceiverSession(
        tmp_path / "inbox", port=0, bind_host="127.0.0.1", lan_host_provider=lambda: "127.0.0.1"
    )
    session.start()
    try:
        offer = session.new_offer()
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        with socket.create_connection(("127.0.0.1", session.port), timeout=5) as raw:
            with context.wrap_socket(raw) as tls:
                leaf = tls.getpeercert(binary_form=True)
        assert leaf is not None
        assert hashlib.sha256(leaf).hexdigest() == offer.tls_certificate_fingerprint
    finally:
        session.stop()
    assert not session.running


def test_busy_preferred_port_falls_back_to_ephemeral(tmp_path: Path) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as blocker:
        blocker.bind(("127.0.0.1", 0))
        blocker.listen()
        busy = blocker.getsockname()[1]
        session = ReceiverSession(
            tmp_path, port=busy, bind_host="127.0.0.1", lan_host_provider=lambda: "127.0.0.1"
        )
        session.start()
        try:
            assert session.port not in (0, busy)
            assert session.new_offer().port == session.port
        finally:
            session.stop()


def test_receiver_id_persists_and_lan_detection_returns_ipv4(tmp_path: Path) -> None:
    first = ReceiverSession(tmp_path).receiver.receiver_id
    assert ReceiverSession(tmp_path).receiver.receiver_id == first
    ipaddress.IPv4Address(detect_lan_ipv4())
