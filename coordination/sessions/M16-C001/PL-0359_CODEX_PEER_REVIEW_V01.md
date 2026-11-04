# PL-0359 Codex Peer Review V01

**Review scope:** Free-first unsigned fallback and simulator/physical-device installation guidance.
**Reviewed documentation revision:** the documentation and tracker commit for PL-0359; final task SHA is recorded by `TASKS.md` and this review's containing commit.
**Verdict:** PASS for PL-0359 documentation scope.

## Source and evidence review

- The updated installation draft identifies the October billing-blocked XCTest result as historical and cites successful 2026-11-04 hosted runs [41743543561](https://github.com/Sekiph82/PackLab/actions/runs/41743543561) and [41754385597](https://github.com/Sekiph82/PackLab/actions/runs/41754385597), each 205/205, 0 failures, 0 skips.
- It distinguishes the unsigned iOS Simulator `.app`, unsigned generic iOS `.xcarchive`, and signed/provisioned physical-device app. It explicitly says neither unsigned output installs directly on iPhone and no IPA was exported.
- It records both artifact IDs, GitHub API SHA-256 digests, sizes, one-day expiry times, source SHAs, toolchain/SDK and intended use. The simulator route requires ZIP digest and embedded provenance verification before installation into the matching simulator.
- Apple-account route is conditional on an authorized Team and valid signing/provisioning. Current Apple guidance is linked for physical-device run/provisioning and registered-device distribution. Personal Team limits and seven-day reprovisioning are stated as current documented limits that must be reconfirmed.
- Windows community sideload/sign tools are described as optional and user-managed; none is bundled, selected or endorsed. The text covers credential/privacy, provenance and provisioning risks.
- `M16_OFFLINE_RELEASE_CONTROL_PREPARATION.md` now distinguishes passed simulator engineering evidence from still-pending signed IPA, physical device, legal and release gates. Its October no-Actions restriction is explicitly historical and superseded by the 2026-11-04 owner authorization; billing and free-storage uncertainty remains.

## Validation and independent review

- `git diff --check`: PASS.
- Lightweight Python text assertions: PASS for the linked run/artifact IDs and digests, one-day expiry, simulator CLI route, physical signing/provisioning requirement, Personal Team limit/caveat, Windows optional/privacy caveat, and current release-status wording.
- Independent docs reviewer: PASS; stale full-suite and October authorization contradictions were corrected.
- Independent tester: PASS; exact run/SHA/artifact records checked against GitHub metadata.
- Independent security reviewer: PASS; no Apple account data, certificates, profiles, private keys, or private scans were added; public artifact exposure and optional Windows tooling are clearly bounded.

## Limitations

- No physical iPhone installation, signed IPA, Windows sideload tool, legal clearance, or release approval was performed or claimed.
- Artifact links are transient and expire one day after upload. Verify current API expiry/digest or rerun the build from reviewed source after expiry.
- PL-0358 remains `EXTERNAL_PENDING_APPLE_SIGNING_CREDENTIALS`; this task documents currently available unsigned routes without claiming that signing blocker is resolved.
