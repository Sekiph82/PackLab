# CLAUDE_PEER_REVIEW: Studio "Receive from iPhone" and Model Viewer (PR #10)

- Reviewer: Claude independent peer reviewer. I did not write this code and did not edit any source.
- Scope: `git diff origin/main...origin/feat/studio-iphone-receiver`, head `4cb4086c` (16 files, +1362/-81).
- CI: Windows Python Quality run 44799347109. I checked it with `gh run view`: `completed/success`, headSha `4cb4086c`.
- What I checked myself:
  - the source diff;
  - the test diff;
  - the offscreen drive script `C:\Users\sekip\Documents\PackLab-work\studio_e2e_offscreen.py`;
  - the screenshots in `C:\Users\sekip\Documents\PackLab-work\studio-e2e`;
  - two of my own probes, run against a `git archive` of the head commit (described below).
- Evidence gathered by the coordinator, which I did not reproduce: the real iPhone scanning the QR and reaching the receiver id, and the 64.8 MB upload/import run.

## Verdict: FAIL (one HIGH finding; everything else is PASS_WITH_NOTES quality)

## Findings

### HIGH
1. **One idle LAN peer can freeze the receiver and hang Studio on close.** Code: `apps/windows-studio/src/packlab_studio/receiver.py:260` and `receiver.py:270-273`.
   - **Cause:** The listening socket is TLS-wrapped (`server.socket = ...wrap_socket(server.socket, server_side=True)`). That means `accept()` runs the TLS handshake synchronously on the single `serve_forever` thread, and nothing sets a timeout. The server now binds `0.0.0.0`.
   - **Effect:**
     - Any device on the Wi-Fi that opens a TCP connection and sends nothing blocks every later client.
     - `stop()` then hangs inside `server.shutdown()`.
     - `CaptureInboxView.shutdown()` runs from `StudioMainWindow.closeEvent` on the UI thread, so the Studio window cannot close.
   - **Reproduced (my probe `dos.py` against the head commit):** I started a `ReceiverSession` on loopback and opened one raw TCP connection that sends nothing. A real TLS client then failed with `TimeoutError: The handshake operation timed out`, and `stop() returned within 5s: False`.
   - **Fix:** wrap with `do_handshake_on_connect=False` and do the handshake in the per-request thread, with a socket timeout (or set a timeout in `get_request`). Add a regression test with an idle peer.

### MEDIUM
2. **`/v1/pair` reads an unauthenticated request body of any size.** Code: `receiver.py:170-172`. `_body()` reads `Content-Length` bytes from an unauthenticated peer with no upper bound and no read timeout. This code already existed, but this PR exposes it to the LAN for the first time: a slowloris attack can exhaust threads, and a large declared length can exhaust memory. Fix: cap the pairing body (for example 16 KiB) and set `timeout` on the handler.
3. **The receiver listens on every interface, and there is no way to stop it.** Code: `receiver_session.py:63` (`bind_host="0.0.0.0"`).
   - Once started, it listens on every interface, including public-profile and VPN adapters, until the app closes.
   - The UI has no Stop button, and `_tick` (`capture_inbox.py:148`) creates a new one-time offer every 120 s for as long as Studio runs.
   - Fix: bind to `lan_host` (the advertised address) and add a Stop action. Also consider limiting how long a receive session runs.

### LOW
4. **The `0o600` mode on the private key has no effect on Windows.** Code: `transfer_security.py:161`. The unencrypted P-256 key is protected only by the inherited `%LOCALAPPDATA%` user ACL. That is acceptable, but it should be documented. Rotation (365 days, renewed 7 days before expiry, regenerated when the SAN no longer matches) is correct and tested.
5. **The session token has a fixed 300 s lifetime with no refresh.** Code: `transfer_security.py:191`. A 65 MB upload expires mid-transfer below roughly 1.8 Mbit/s of effective throughput. NOT_VERIFIED: whether the iOS client re-pairs or resumes after an `expired_pairing` response on a chunk.
6. **The PLY loader does not bound element counts.** Code: `viewport.py:322` (`np.empty(count)`).
   - My probe `ply.py` declared `element face 100000000000`. It raised `MemoryError (745 GiB)`.
   - That error escapes `ModelViewerView.load`, which catches only `ViewportLoadError` (`model_viewer.py:100`).
   - A negative count is correctly rejected as truncated.
   - Fix: reject counts that the file length cannot hold.
7. **Some work runs on the UI thread.** Model loads, `.packscan` import (`capture_inbox.py:183`, acknowledged with a `ponytail:` note) and the once-per-second index read in `refresh_inbox` all run on the UI thread. Acceptable for V1, but a 65 MB import freezes the window.
8. **Expired offers are never pruned.** They pile up in `PairingStore._offers`, one every 120 s. Negligible.
9. **The screenshots do not show text.** The offscreen screenshots render no fonts (every label is a box glyph). The status and inbox text is backed only by the script's stdout, not by the images. The 192k-point colored PLY render (05/06) is genuine visual evidence.
10. **The license register entries are present, but the release work is open.** `cryptography` 45.0.7 is Apache-2.0 OR BSD-3 and bundles OpenSSL; `segno` 1.6.6 is BSD-3. The register states correctly that frozen-build notice inventory is still pending.

## Correctness confirmed
- **Splat projection:** it is algebraically identical to `_project`, because the `scale/d*d` factors cancel.
- **ARGB packing:** correct, and `buffer` outlives `drawImage`.
- **LOD stride:** it keeps colors aligned with points.
- **Binary PLY:**
  - truncation checks happen before `frombuffer`;
  - big-endian files are rejected as UNSUPPORTED;
  - face indices are validated.
- **Port and pairing:**
  - `SO_EXCLUSIVEADDRUSE` works, and the fallback to an ephemeral port is tested;
  - the QR carries the real port;
  - the pin test compares the served leaf certificate's SHA-256 against the offer, the same way iOS does;
  - pairing replay is blocked by `_used`.
- **Import path traversal:** the file picker gives an owner-chosen local path, and contents go through the existing `ImportService` and quarantine. The run quarantined the corrupt phone file as `corrupt_zip`, as expected.
- **Capture Inbox without a project:** tested. The `test_m06_r01` index shift (1 to 2) matches the change.
- **Test quality:** good. The tests make a real HTTPS loopback pair+upload through the view and check a real certificate for iOS rules. There are no tests for an idle peer, an oversized body or token expiry during an upload.

## NOT_VERIFIED
- Windows Firewall prompt behavior.
- A real iPhone completing an upload (blocked until PR #9 ships `NSLocalNetworkUsageDescription`).
- Performance with large meshes.
