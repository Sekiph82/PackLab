# PackLab | iPhone 16 Installation and Safe Rollback (DOCUMENTATION DRAFT, NOT DEVICE-VALIDATED)

**Prepared 2026-10-15; updated 2026-11-04 after owner authorization for hosted Actions.**
Relates to **PL-0359, PL-0362 and PL-0367 documentation preparation**. This document is not a release, factory install approval or proof of a physical device installation. The October no-Actions instruction was superseded by the owner's 2026-11-04 autonomous-execution authorization; the no-secret, licensing, legal and physical acceptance boundaries remain.

## Source-grounded current identities

| Contract / component | Source inspected | Observed value |
| --- | --- | --- |
| Capture bundle ID | `apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj` | `com.packlab.capture` |
| Capture marketing version / build | Same project | `MARKETING_VERSION=0.1.0`, `CURRENT_PROJECT_VERSION=1` (observed source values, not released product) |
| Deployment target | Same project | iOS 17.0 minimum |
| NextLevel dependency | Same project + `docs/development/NEXTLEVEL_PIN.md` | Exact 0.19.1 (upstream Swift5 manifest compatibility adjustment used in CI; not part of shipping release identity) |
| App permission | Current `apps/ios-capture/PackLabCapture/Info.plist` | `NSCameraUsageDescription` present; no locally verified on-device permission behavior |
| PackScan format | `docs/packscan/container-layout.md`, `docs/packscan/manifest-contract.md`, `schemas/packscan/manifest.schema.json` | Evidence ZIP, schema 1.0.0, SHA-256 index, original `images/` immutable |
| Device testing | `docs/development/IOS_BASELINE.md`, `docs/development/IOS_SIMULATOR_FALLBACKS.md` | Target is iPhone 16 Standard, no mandatory LiDAR; physical camera/AR/motion require device acceptance |

**Historical CI blocker:** The 2026-10-15 run was billing-blocked as recorded in the historical audit. It was superseded on 2026-11-04 by successful full-suite hosted macOS runs [PL-0354 run 41743543561](https://github.com/Sekiph82/PackLab/actions/runs/41743543561) and [PL-0357 run 41754385597](https://github.com/Sekiph82/PackLab/actions/runs/41754385597), both reporting 205/205 XCTest, 0 failures and 0 skips.

**Current device/signing limit:** The latest hosted build evidence is simulator-only or an unsigned generic iOS archive. GitHub currently reports the repository as PUBLIC, with zero repository signing secrets and zero configured environments. No signed IPA, physical iPhone installation, Apple account/device acceptance, or distribution approval exists in this evidence.

## PL-0359 free-first build artifacts and simulator route

The public GitHub Actions artifacts are short-lived CI outputs. A signed-in GitHub user with repository read access can download workflow artifacts, so no certificate, provisioning profile, private key, Apple account data, private scan or supplier file may be placed in these artifacts. See [GitHub's artifact download access rules](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts).

| Artifact | Verified evidence | Intended use | Physical iPhone installation |
| --- | --- | --- | --- |
| Unsigned simulator `.app` | [Run 41752044382](https://github.com/Sekiph82/PackLab/actions/runs/41752044382), source `384eaef996c92b31d39a28581c0ea6dc7da3d905`; artifact `13286072651`, 2,228,647 bytes, SHA-256 `21a730c4ae4e9a24bc1823ae5f7c6f0ee6e857401417dc614667b14820140e35`, expires `2026-11-05T01:16:12Z`; macOS 15.8.2, Xcode 16.0 / 16A242d, iPhone 16 / iOS 18.0 simulator; 205/205 XCTest | Install into the matching iOS Simulator on macOS for CI/debug inspection | **No.** Simulator architecture/runtime product is not a device-installable app. |
| Unsigned generic iOS `.xcarchive` | [Run 41754385597](https://github.com/Sekiph82/PackLab/actions/runs/41754385597), source `b94e73744544feae7f5dddcdbfbef22c2cab392d`; artifact `13287651642`, 5,380,516 bytes, SHA-256 `dc7716143c52785bf6b2d0045a37e3d41f36a6a2d9367ab56703a51d288b3196`, expires `2026-11-05T01:31:32Z`; Capture 0.1.0/build 1; iPhoneOS SDK 18.0; manifest states `UNSIGNED`; profile/signature checks passed | Inspect an unsigned device-target archive or use as a source for a separately authorized signing process | **No.** No IPA was exported; an unsigned archive is not an installable iPhone package. |

Both artifact types use one-day retention and expire one day after upload; they may have expired by the time a reader uses this document. Check the workflow run's current Artifacts section before download. Verify the downloaded artifact ZIP's SHA-256 against the digest above, then verify the embedded provenance manifest. If expired, rerun the appropriate workflow against the reviewed source revision; never substitute a different SHA without checking its provenance. The archive and simulator artifacts are build evidence, not retained release candidates.

### Install the simulator app on macOS

1. Download `packlab-capture-unsigned-simulator-<source-sha>` from the linked PL-0356 workflow run while it is available. Verify the artifact ZIP digest from the table, then check `packlab-capture-simulator-provenance.txt` matches the source SHA, run, bundle ID, simulator destination and lockfile digest.
2. Install a matching iOS 18.0 Simulator runtime and boot an iPhone 16 simulator in Xcode. Find the booted device identifier with `xcrun simctl list devices booted`.
3. Install and launch the simulator product using that simulator's UDID:

   ```sh
   xcrun simctl install <DEVICE_UDID> /path/to/PackLabCapture.app
   xcrun simctl launch <DEVICE_UDID> com.packlab.capture
   ```

   Alternatively, open the project in Xcode, select the iPhone 16 simulator and use Product > Run. This route exercises the simulator build only; it does not validate iPhone hardware, camera behavior, physical performance, signing, or distribution.

### Physical iPhone route

A physical iPhone requires a device-target app signed with a valid development/distribution certificate and provisioning profile suitable for the app and device. The unsigned simulator `.app` and unsigned `.xcarchive` cannot be installed directly.

On a Mac, the owner can open `apps/ios-capture/PackLabCapture.xcodeproj`, add an Apple Account in Xcode, select the iPhone as the run destination, select an authorized Team, and let Xcode manage signing/provisioning if Apple permits it for that account, app ID and capabilities. Apple documents device registration and automatic development-profile creation in [Running your app on simulated or physical devices](https://developer.apple.com/documentation/Xcode/running-your-app-on-simulated-or-physical-devices). A development profile is tied to the app ID, signing certificate and registered device(s); see [Apple's development provisioning profile requirements](https://developer.apple.com/help/account/provisioning-profiles/create-a-development-provisioning-profile).

Apple currently documents limited Personal Team provisioning for local testing: up to 10 App IDs and 3 devices, with those registrations and profiles expiring after 7 days; apps must be rebuilt/reinstalled after profile expiry. Limits and account eligibility must be reconfirmed in current Xcode/Apple documentation before use. This is a local test route, not App Store/TestFlight distribution approval; distribution requires an eligible Apple Developer Program team and its applicable signing/distribution process. See [Apple's developer account overview](https://developer.apple.com/help/account/basics/about-your-developer-account) and [registered-device distribution guidance](https://developer.apple.com/documentation/xcode/distributing-your-app-to-registered-devices).

No Windows-side signing/sideload tool is included, bundled, selected or endorsed by PackLab. If the owner chooses a community Windows tool, that is an optional user-managed route outside PackLab support and Apple-official tooling. Obtain it only from its verified publisher, review how it handles Apple Account authentication, signing keys and provisioning data, never give it credentials unless the owner has independently accepted that risk, and verify the resulting IPA's signature, profile, bundle ID, version/build and provenance. Tool availability, privacy practices, Apple policy compatibility and profile expiry may change. A Windows tool cannot make the unsigned simulator app or archive installable without valid signing/provisioning.

## Future approved installation, before any operation

1. **Prerequisite authorization:** Require formally reviewed redistribution rights, owner acceptance of the intended physical test, confirmed PackLab Capture signing/provisioning route, exact release artifact/source identities and SHA-256. Do not use an unsigned simulator .app or .xcarchive as an installable physical iPhone package.
2. **Backup first:** Identify existing original `.packscan` sessions on the device and use an approved PackLab export/share/transfer mechanism to export every authoritative package before app removal. Verify the exported package file length, manifest schema, checksum index and each payload hash in an independent safe location; record confirmation **without** attaching private images/scans to CI, tickets or the repository. If export, verification or user-data restore semantics are uncertain, STOP before delete/uninstall.
3. **Trust and signing:** A macOS/Xcode installation requires a suitable Apple signing team/account and any provisioning necessary for this particular device/bundle. A personal/free Apple team may have limitations or expiry, which must be confirmed with current Apple tooling. Never collect the owner's Apple account password, private key, provisioning profile or device identifiers into GitHub logs/prompt.
4. **Mac + Xcode route:** Open the source `apps/ios-capture/PackLabCapture.xcodeproj`; use a supported Xcode version, physical iPhone 16 as run destination and select the owner's authorized signing team. On iPhone, accept computer trust prompts and enable Developer Mode when required by OS policy, then build/run a **properly signed** app. Read and record installed bundle ID, version/build and provenance after install. This route has not been executed or validated here.
5. **Signed artifact route:** Only an explicitly accepted and correctly signed/provisioned distribution artifact may be installed via a device-management or Apple-supported distribution route for which the owner has rights. Unsigned Xcode Simulator binaries will not install directly on an iPhone.
6. **First launch:** Confirm build identity and source revision using declared UI/about/diagnostic features once implemented; check camera permission against `Info.plist`. Local-network permission should only be prompted if current live app transport requires it; historical permission documents may predate later transfer code. Test permissions and transfer end-to-end on the real device before asserting success.
7. **Reinstall/upgrade:** Prefer an app update path that preserves the same bundle identity and on-device container. Do NOT assume it always preserves data across signing-team changes, app removal, failed upgrade, re-provisioning, or container migration. Reverify original `.packscan` packages after update. A destructive uninstall is forbidden until the export-and-hash backup gate passes.

## Schema incompatibility and rollback

- Compare **three independent domains**: `StudioVersion`, `CaptureVersion`, and `PackScanSchemaVersion`, per `docs/architecture/VERSIONING_POLICY.md`. Do not equate their numeric versions.
- On unsupported `.packscan` schema, STOP ingestion and report observed exact version, supported reader range, original SHA-256 and diagnostic category. Do not guess version compatibility or silently rewrite manifest/schema/coordinate semantics.
- Snapshot/copy original capture evidence and its complete checksum-valid ZIP to read-only, owner-controlled backup. Never modify `images/`, timestamps, calibration or manifest in place.
- Rollback may restore a separately verified application build or derived representation; it must never restore over, rewrite, or delete the immutable original `.packscan` package or its original image bytes.
- For a **declared and implemented** migration, produce a **new derived** output with an explicit source/target schema path and retained original package; otherwise do not convert.
- Select a previously owner-approved Studio/Capture build **only by reviewed release manifest, original source SHA, artifact/executable hash, version/build, dependencies and schema compatibility**. Do not substitute an arbitrary old Installer or privately downloaded IPA.
- Before downgrading Capture, export and verify every current package and application state the older version may not understand. An older binary is **not assumed able to read newer projects or schema**.
- Restore from the last independently verified package/library backup if needed. Do not recommend deleting original device sessions, overwriting unbacked libraries or modifying the source package to force compatibility.
- Finally test reinstall, camera permission, offline transfer, project reopening, original data integrity, app build identity and roundtrip on the **real device**. Without executed evidence report **NOT_VALIDATED**, not PASS.

## Safe failure codes for future tooling

`BACKUP_NOT_VERIFIED`, `INVALID_PACKSCAN_CHECKSUM`, `UNSUPPORTED_SCHEMA_VERSION`, `MIGRATION_PATH_NOT_DECLARED`, `APP_SIGNING_NOT_AVAILABLE`, `APPLE_PROVISIONING_EXPIRED`, `BUILD_IDENTITY_UNKNOWN`, `ROLLED_BACK_WITH_UNVERIFIED_DEVICE_STATE`. Do not emit private absolute filesystem paths, owner identifiers, keychain contents, package bytes or scans into logs.

## Remaining real task work after owner lift

Confirm application data export and permission semantics against current iOS code, execute controlled physical iPhone testing, resolve formal license/legal review and security gates, and complete PL-0362/0367 device/release acceptance independently. Hosted simulator CI has passed 205/205 on runs 41743543561 and 41754385597; that does not satisfy physical-device or signed-distribution acceptance. This file itself does **not** close PL-0362 or PL-0367.
