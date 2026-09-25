from __future__ import annotations

import json
from pathlib import Path


def test_production_swift_client_consumes_the_shared_transfer_contract(repo_root: Path) -> None:
    fixture = json.loads((repo_root / "tests/fixtures/transfer-protocol-v1-golden.json").read_text(encoding="utf-8"))
    swift_protocol = (repo_root / "apps/ios-capture/PackLabCapture/Services/TransferProtocol.swift").read_text(encoding="utf-8")
    swift_client = (repo_root / "apps/ios-capture/PackLabCapture/Services/TransferService.swift").read_text(encoding="utf-8")
    for field in ("receiver_id", "transfer_id", "capture_id", "package_name", "total_bytes", "package_sha256"):
        assert field in swift_protocol
        assert field in json.dumps(fixture["create"])
    for route in ("/v1/pair", "/v1/transfers", "/complete", "/chunks"):
        assert route in swift_client
    for model in ("TransferStatusMessage", "TransferControlMessage", "TransferCompletionAcknowledgement", "TransferErrorEnvelope"):
        assert f"struct {model}" in swift_protocol
