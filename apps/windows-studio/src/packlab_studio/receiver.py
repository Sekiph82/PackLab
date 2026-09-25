"""Headless HTTPS PackLab Transfer V1 receiver."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from packlab_core.pairing import PairingOffer, PairingStore
from packlab_core.transfer_protocol import TransferProtocolError
from packlab_core.transfer_security import (
    PairingAuthenticator,
    TLSIdentity,
    create_server_tls_context,
)

from .ingest import ImportResult, ImportService
from .quarantine import QuarantineStore
from .transfer_store import ReceiverTransferState, ResumableTransferStore


class ReceiverError(RuntimeError):
    pass


class PackLabReceiver:
    def __init__(self, root: str | Path, *, receiver_id: str | None = None, host: str = "127.0.0.1", port: int = 0, tls_identity: TLSIdentity | None = None, certificate_fingerprint: str | None = None) -> None:
        self.root = Path(root)
        self.host = host
        self.port = port
        self.receiver_id = receiver_id or uuid.uuid4().hex
        self.tls_identity = tls_identity
        self._pin = certificate_fingerprint or (tls_identity.fingerprint if tls_identity else None)
        self.pairings = PairingStore()
        self.authenticator = PairingAuthenticator(self.pairings, clock=__import__("time").time)
        self.transfers = ResumableTransferStore(self.root / "transfers")
        self.inbox = self.root / "capture_inbox"
        self.ingest = ImportService(quarantine=QuarantineStore(self.root / "quarantine"))
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def pairing_offer(self, *, host: str | None = None, ttl_seconds: int = 120) -> PairingOffer:
        if not self._pin:
            raise ReceiverError("TLS identity must be configured before pairing")
        return self.pairings.create_offer(receiver_instance_id=self.receiver_id, host=host or self.host, port=self.port, tls_certificate_fingerprint=self._pin, ttl_seconds=ttl_seconds)

    def pair(self, offer: PairingOffer, *, code: str, certificate_fingerprint: str):
        return self.authenticator.authenticate_pairing(offer, receiver_instance_id=self.receiver_id, pairing_code=code, certificate_fingerprint_value=certificate_fingerprint)

    def start(self) -> None:
        if self._server is not None:
            return
        if self.tls_identity is None:
            raise ReceiverError("HTTPS TLS identity is required")
        receiver = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "PackLabTransfer/1"

            def log_message(self, format: str, *args: Any) -> None:
                return

            def _json(self, status: int, value: object) -> None:
                body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _auth(self) -> None:
                token = self.headers.get("Authorization", "")
                if not token.startswith("Bearer "):
                    raise TransferProtocolError("unpaired", "authorization is required")
                receiver.authenticator.require_session(receiver_instance_id=receiver.receiver_id, token=token[7:], certificate_fingerprint_value=receiver._pin or "")

            def _body(self) -> dict[str, object]:
                length = int(self.headers.get("Content-Length", "0"))
                value = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(value, dict):
                    raise TransferProtocolError("bad_request", "JSON object required")
                return value

            def do_POST(self) -> None:
                try:
                    self._auth()
                    if self.path == "/v1/transfers":
                        self._json(HTTPStatus.CREATED, asdict(receiver.create_transfer(self._body(), token_authenticated=True)))
                    elif self.path.startswith("/v1/transfers/") and self.path.endswith("/cancel"):
                        transfer_id = self.path.split("/")[3]
                        self._json(HTTPStatus.OK, asdict(receiver.cancel(transfer_id, token_authenticated=True)))
                    elif self.path.startswith("/v1/transfers/") and self.path.endswith("/chunks"):
                        transfer_id = self.path.split("/")[3]
                        offset = int(self.headers["X-PackLab-Offset"])
                        digest = self.headers["X-PackLab-Chunk-SHA256"]
                        length = int(self.headers.get("Content-Length", "0"))
                        self._json(HTTPStatus.OK, asdict(receiver.put_chunk(transfer_id, offset=offset, payload=self.rfile.read(length), chunk_sha256=digest, token_authenticated=True)))
                    elif self.path.startswith("/v1/transfers/") and self.path.endswith("/complete"):
                        transfer_id = self.path.split("/")[3]
                        self._json(HTTPStatus.OK, asdict(receiver.complete(transfer_id, token_authenticated=True)[0]))
                    else:
                        self._json(HTTPStatus.NOT_FOUND, {"error_code": "unknown_route"})
                except (TransferProtocolError, ReceiverError, ValueError, KeyError) as error:
                    self._json(HTTPStatus.BAD_REQUEST, {"error_code": getattr(error, "code", "bad_request"), "error": str(error).split(":", 1)[0]})

            def do_GET(self) -> None:
                try:
                    self._auth()
                    parsed = urlparse(self.path)
                    if parsed.path.startswith("/v1/transfers/"):
                        transfer_id = parsed.path.split("/")[3]
                        self._json(HTTPStatus.OK, asdict(receiver.status(transfer_id, token_authenticated=True)))
                    else:
                        self._json(HTTPStatus.NOT_FOUND, {"error_code": "unknown_route"})
                except (TransferProtocolError, ReceiverError, ValueError, KeyError) as error:
                    self._json(HTTPStatus.BAD_REQUEST, {"error_code": getattr(error, "code", "bad_request"), "error": str(error).split(":", 1)[0]})

        server = ThreadingHTTPServer((self.host, self.port), Handler)
        server.socket = create_server_tls_context(self.tls_identity).wrap_socket(server.socket, server_side=True)
        self._server = server
        self.port = int(server.server_address[1])
        self._thread = threading.Thread(target=server.serve_forever, name="packlab-receiver", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        if self._thread:
            self._thread.join(timeout=2)
        self._server = None
        self._thread = None

    def status(self, transfer_id: str, *, token_authenticated: bool = False):
        self._require_direct_auth(token_authenticated)
        return self.transfers.status(transfer_id)

    def create_transfer(self, value: dict[str, object], *, token_authenticated: bool = False) -> ReceiverTransferState:
        self._require_direct_auth(token_authenticated)
        from packlab_core.transfer_protocol import TransferCreate

        request = TransferCreate.from_dict(value)
        if request.receiver_id != self.receiver_id:
            raise TransferProtocolError("wrong_receiver", "transfer targets another receiver")
        return self.transfers.create(request)

    def put_chunk(self, transfer_id: str, *, offset: int, payload: bytes, chunk_sha256: str, token_authenticated: bool = False):
        self._require_direct_auth(token_authenticated)
        return self.transfers.put_chunk(transfer_id, offset=offset, payload=payload, chunk_sha256=chunk_sha256)

    def cancel(self, transfer_id: str, *, token_authenticated: bool = False):
        self._require_direct_auth(token_authenticated)
        return self.transfers.cancel(transfer_id)

    def complete(self, transfer_id: str, *, token_authenticated: bool = False) -> tuple[object, ImportResult | None]:
        self._require_direct_auth(token_authenticated)
        verification = self.transfers.verify(transfer_id)
        if not verification.verified:
            return self.transfers.completion_ack(transfer_id, authenticated=True), None
        destination = self.inbox / f"{transfer_id}.packscan"
        published = self.transfers.publish_verified(transfer_id, destination)
        result = self.ingest.import_path(published, source_channel="network")
        return self.transfers.completion_ack(transfer_id, authenticated=True), result

    def _require_direct_auth(self, token_authenticated: bool) -> None:
        if not token_authenticated:
            raise TransferProtocolError("unpaired", "authenticated receiver session is required")
