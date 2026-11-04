# PL-0364 | Release Manifest Contract V1

## Purpose and status

`schemas/release/release-manifest.schema.json` defines the generated machine-readable output. `tools/release/offline_release_manifest.py` validates source/build evidence references and emits deterministic canonical JSON. It is a preparation artifact only: generated output is always `PREPARATION_ONLY_NOT_RELEASE_AUTHORIZATION`, `release_authorization: NOT_GRANTED`, and `m17_status: NOT_ACCEPTED`. The tool does not build, sign, verify a signature cryptographically, publish, or authorize a release.

The source versions and release-train identity come from `offline_version_inventory.py` at the exact current Git HEAD. The candidate input must repeat that source commit, train ID, and exact independent Studio, Capture/build, and PackScan versions. Version mismatch or a modified authoritative version source blocks generation. Dependency/toolchain sources (`pyproject.toml`, Xcode project and `Package.resolved`, Windows native-source lock, and OCCT build contract) are also read from and blob-checked against that exact commit; `Package.resolved` digest is bound into iOS build and artifact receipts. OCCT version is derived from the pinned native-source lock and checked against the build contract.

## Required candidate evidence

The UTF-8 JSON candidate input has exactly these top-level fields:

| Field | Required source |
| --- | --- |
| `source_commit`, `release_train_id`, `versions` | Exact output from the current source version inventory. |
| `artifacts` | At least one Windows and one iOS artifact, each pointing to a digest-bound JSON provenance receipt. Receipt source SHA, platform, name, kind, digest, byte length, workflow run, and signing state are checked. |
| `windows_build_identity`, `ios_build_identity` | Digest-bound JSON receipts tied to the same platform artifact source SHA, workflow run ID, and complete artifact digest set. Windows records observed Python, Qt, OCP, OCCT, and Open3D. iOS records Xcode version/build, SDK, Swift language mode and compiler version, and NextLevel version/revision. Locked/source declarations are cross-checked where they are authoritative. |
| `packscan_compatibility` | Read minimum/maximum, write version, migrations list, and a content-digest-bound compatibility-policy reference. Current source only validates exact `1.0.0` reads/writes and no migrations; broader claims fail closed. |
| `third_party_notice_inventory` | Path and SHA-256 of the third-party license/notice inventory reference. This records provenance only and does not grant legal clearance. |
| `known_limitations` | Unique machine-readable limitation codes; `m17_not_accepted` is mandatory. |

All references are normalized repository-relative paths. Absolute paths, drive paths, UNC paths, URLs, backslashes, empty/dot/dot-dot components, missing files, symlink/junction traversal, malformed digests, and digest mismatches are rejected. JSON build/provenance references have strict field allowlists. The generator emits redacted error codes and does not echo candidate values.

For `SIGNED_VERIFIED`, the artifact receipt must reference a separate digest-bound verifier record matching the artifact digest and signature digest and carrying `SIGNATURE_VERIFIED` plus a verifier tool identifier. `UNSIGNED` records cannot carry signature evidence. This structural check binds the cited verifier record; it does not independently execute the verifier or inspect signing keys/certificates. Keep signing identities generic and never include Apple IDs, UDIDs, profiles, keychains, certificates, tokens, or private key material.

The manifest identity is SHA-256 over canonical sorted JSON of the version tuple, exact source SHA, artifact/build/compatibility/notice digests and facts, and limitations. It excludes evidence file paths and timestamps. Artifact and migration collections are normalized before hashing. The output still carries logical relative paths and evidence digests for traceability.

## Current evidence boundary

Current source declares Studio `0.1.0`, Capture `0.1.0` build `1`, PackScan schema `1.0.0`; the release train remains the PL-0363 source identity. The PackScan implementation reads and writes only schema `1.0.0`; no migration implementation is present. The source lock declarations include Python `>=3.12,<3.13`, PySide6 Essentials/Addons `6.11.2`, OCP binding `7.9.3.1.1`, OCCT `7.9.3`, and Open3D `0.20.0`; iOS source pins NextLevel `0.19.1` at revision `edb3ba52aed8b49e9e197a275ea5e4846fb8c36d` and Swift language mode `6.0`.

These are declared/locked facts, not proof that a complete Windows and iOS artifact set with matching current-source build receipts and complete distribution notices exists. No PL-0364 production manifest is checked in. PL-0361's historical iOS outputs are unsigned simulator/archive products from a different source commit; the simulator app and archive are not a signed device release. The retained PL-0352 Windows installer comes from an older source commit and a private historic retention chain; it is not a current-source paired artifact and is not public release evidence. Formal legal review, Apple signing credentials, physical-device acceptance, M17 acceptance, and PL-0368 release authorization remain open.

Run against a complete, reviewed evidence description:

```powershell
uv run --locked python tools/release/offline_release_manifest.py <candidate.json> --repo . --output <manifest.json>
```

If any required reference or source/build binding is missing, the command exits `2`, prints only a `BLOCKED` status and stable error codes, and writes no manifest. A synthetically complete test fixture proves validator behavior only; it is not artifact, signing, audit, legal, or release evidence.
