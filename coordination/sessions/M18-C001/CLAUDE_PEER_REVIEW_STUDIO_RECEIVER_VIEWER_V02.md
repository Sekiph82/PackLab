# CLAUDE_PEER_REVIEW V02: Studio receiver and viewer (PR #10, commit aaa1da7c)

- **Reviewer:** Claude, acting as independent peer reviewer. I did not write this code and did not edit any source.
- **Scope:** `git diff 4cb4086c aaa1da7c`. It touches `receiver.py`, `capture_inbox.py` and two test files. It answers my V01 review.
- **CI (my own check with `gh run view`):** Windows Python Quality run 44806018215 on head `aaa1da7c` is **FAILURE**: 1 failed, 3370 passed, 18 skipped.
  - Failing test: `tests/transfer/test_loopback_receiver.py::test_oversized_unauthenticated_body_is_rejected`.
  - Error: `http.client.RemoteDisconnected: Remote end closed connection without response`.
  - Signing Material Guard run 44806018255: success.

## Verdict: FAIL, because CI is red. The security fixes themselves are verified.
The source changes resolve the V01 HIGH finding and both MEDIUM findings. The PR cannot merge until the new test, or the rejection path behind it, passes on the Windows runner.

## How the V01 findings stand
- **HIGH 1 (an idle peer blocks pairing and `stop()`): RESOLVED.**
  - The TLS handshake now runs in `_ExclusiveHTTPServer.finish_request`, once per connection, with a 30 s socket timeout (`receiver.py:56-74`).
  - `daemon_threads=True` and `block_on_close=False` are set.
  - The listening socket is no longer wrapped.
  - I re-ran my repro (`dos.py`) against a `git archive` of aaa1da7c. With one idle TCP peer open, a real TLS client completed its handshake and `stop()` returned within 5 s. On 4cb4086c the same repro made the client time out and `stop()` hang.
  - The new test `test_idle_lan_peer_cannot_block_pairing_or_stop` covers the right behavior. Its time bounds are 5 s for pairing and 3 s for stop.
- **MEDIUM 2 (unbounded unauthenticated body): RESOLVED in source; the test fails on CI.**
  - Source: the JSON body is capped at 64 KiB and chunks at 8 MiB, and negative lengths are rejected (`receiver.py:203-204` and `:246-247`). The iOS client sends 256 KiB chunks (`TransferService.swift:56`), well under the 8 MiB cap.
  - **Root cause of the CI failure:** the handler rejects the request without reading the 128 KiB body, and the connection closes with unread data still in the receive buffer. Windows then sends a TCP RST instead of FIN, so the client loses the 400 response before it reads it. The rejection itself works, which is the security property.
  - The test passed 3 of 3 times on my machine. I ran it with the head's source on `PYTHONPATH`, but `uv run` may have picked up the installed editable checkout instead, so that local pass is not proof against this race.
  - **Fix (pick one):**
    - (a) On rejection, set `close_connection = True` and drain a bounded amount (for example up to 1 MiB), or call `shutdown(SHUT_WR)` before closing.
    - (b) Make the test accept either `HTTPError` 400 or `ConnectionResetError`/`RemoteDisconnected`, and assert that the receiver is still running and can still pair.
- **MEDIUM 3 (always listening): RESOLVED as a merge blocker.**
  - The new "Stop receiving" button stops the timer, stops the session and clears the offer and QR. The capture-inbox test asserts this.
  - The receiver still binds `0.0.0.0`. I downgrade this to a LOW follow-up: listening is now an explicit owner action, pairing needs a one-time offer shown on screen, and TLS is pinned.

## LOW follow-ups (not merge-blocking)
- Bind to the advertised `lan_host` instead of `0.0.0.0`.
- The private key's `0o600` mode has no effect on Windows, so document that it relies on the `%LOCALAPPDATA%` ACL.
- The fixed 300 s session token has no refresh, which makes slow-link uploads fail.
- PLY element counts are not checked against file length (`viewport.py:322`): a huge count raises a `MemoryError` that escapes `ModelViewerView.load`.
- File import, model loading and the once-per-second inbox refresh run on the UI thread.
- Expired pairing offers are never pruned.
- The frozen-build license and OpenSSL notice inventory is not done yet.
- New in V02:
  - Handler threads are daemon threads with `block_on_close=False`. A chunk write in flight can be cut off when the app exits; the resumable store should tolerate this, but no test checks it.
  - The idle-peer test calls `_pair` without a client timeout, so on a regression it would hang instead of failing quickly.

## NOT_VERIFIED
- Windows Firewall prompt behavior.
- A real iPhone completing an upload end to end. This needs PR #9 installed on the device.
