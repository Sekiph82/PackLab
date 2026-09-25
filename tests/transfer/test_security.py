from __future__ import annotations

import pytest

from packlab_core.pairing import PairingStore
from packlab_core.transfer_protocol import TransferProtocolError
from packlab_core.transfer_security import PairingAuthenticator


def _authenticator(now: list[float]) -> tuple[PairingStore, PairingAuthenticator]:
    pairing = PairingStore(clock=lambda: now[0])
    return pairing, PairingAuthenticator(pairing, clock=lambda: now[0], session_ttl_seconds=30)


def test_pairing_issues_scoped_credential_and_authentication_requires_https_pin() -> None:
    now = [100.0]
    pairing, authenticator = _authenticator(now)
    offer = pairing.create_offer(receiver_instance_id="r", host="localhost", port=8443, tls_certificate_fingerprint="pin")
    credential = authenticator.authenticate_pairing(offer, receiver_instance_id="r", pairing_code=offer.pairing_code, certificate_fingerprint_value="pin")
    authenticator.require_session(receiver_instance_id="r", token=credential.token, certificate_fingerprint_value="pin")
    with pytest.raises(TransferProtocolError, match="insecure_transport"):
        authenticator.require_session(receiver_instance_id="r", token=credential.token, certificate_fingerprint_value="pin", transport="http")
    with pytest.raises(TransferProtocolError, match="wrong_pin"):
        authenticator.require_session(receiver_instance_id="r", token=credential.token, certificate_fingerprint_value="other")
    assert credential.token not in repr(credential.receiver_instance_id)


def test_missing_expired_revoked_and_wrong_receiver_credentials_fail_closed() -> None:
    now = [100.0]
    pairing, authenticator = _authenticator(now)
    offer = pairing.create_offer(receiver_instance_id="r", host="localhost", port=8443, tls_certificate_fingerprint="pin")
    credential = authenticator.authenticate_pairing(offer, receiver_instance_id="r", pairing_code=offer.pairing_code, certificate_fingerprint_value="pin")
    with pytest.raises(TransferProtocolError, match="unpaired"):
        authenticator.require_session(receiver_instance_id="r", token="unknown", certificate_fingerprint_value="pin")
    with pytest.raises(TransferProtocolError, match="wrong_receiver"):
        authenticator.require_session(receiver_instance_id="other", token=credential.token, certificate_fingerprint_value="pin")
    now[0] = 131.0
    with pytest.raises(TransferProtocolError, match="expired_pairing"):
        authenticator.require_session(receiver_instance_id="r", token=credential.token, certificate_fingerprint_value="pin")
