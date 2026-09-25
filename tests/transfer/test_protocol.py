"""Cross-language PackLab Transfer Protocol V1 contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from packlab_core.transfer_protocol import (
    PROTOCOL_NAME,
    PROTOCOL_VERSION,
    TransferCreate,
    TransferProtocolError,
)


def test_golden_create_message_round_trips() -> None:
    fixture = Path(__file__).parents[1] / "fixtures" / "transfer-protocol-v1.json"
    value = json.loads(fixture.read_text(encoding="utf-8"))
    request = TransferCreate.from_dict(value)
    assert request.to_dict() == value
    assert request.protocol_version == PROTOCOL_VERSION
    assert PROTOCOL_NAME == "packlab-transfer"


@pytest.mark.parametrize("field", ["receiver_id", "transfer_id", "capture_id", "package_name"])
def test_required_identity_fields_are_rejected_when_missing(field: str) -> None:
    value = {
        "message": "create_transfer",
        "protocol": PROTOCOL_NAME,
        "protocol_version": PROTOCOL_VERSION,
        "transport": "https",
        "receiver_id": "r",
        "transfer_id": "t",
        "capture_id": "c",
        "package_name": "c.packscan",
        "total_bytes": 1,
        "package_sha256": "a" * 64,
    }
    value.pop(field)
    with pytest.raises(TransferProtocolError) as error:
        TransferCreate.from_dict(value)
    assert error.value.code == "bad_request"


def test_future_version_and_insecure_transport_fail_closed() -> None:
    base = {
        "message": "create_transfer",
        "protocol": PROTOCOL_NAME,
        "protocol_version": "2",
        "transport": "https",
        "receiver_id": "r",
        "transfer_id": "t",
        "capture_id": "c",
        "package_name": "c.packscan",
        "total_bytes": 1,
        "package_sha256": "a" * 64,
    }
    with pytest.raises(TransferProtocolError, match="unsupported_version"):
        TransferCreate.from_dict(base)
    base["protocol_version"] = PROTOCOL_VERSION
    base["transport"] = "http"
    with pytest.raises(TransferProtocolError, match="insecure_transport"):
        TransferCreate.from_dict(base)
