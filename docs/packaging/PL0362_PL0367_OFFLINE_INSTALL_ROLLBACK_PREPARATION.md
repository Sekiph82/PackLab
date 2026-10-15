# PackLab | iPhone 16 Installation and Safe Rollback (OFFLINE DRAFT, NOT DEVICE-VALIDATED)

**Prepared 2026-10-15 without GitHub Actions, CI runners or an iPhone.**
Relates to **PL-0359, PL-0362 and PL-0367 documentation preparation only**. NOT a completed/audited task, release, authorized factory install or proof of an actual device installation. The owner prohibited new Actions spend until at least November and requires explicit reauthorization.

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

**Current blocker:** GitHub macOS latest final 205-test run did NOT execute because of Actions account billing lock. A targeted 25/25 XCTest run passed, but no full suite accepted; there is no signed physical iPhone app or approved distribution channel in this evidence.

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
- For a **declared and implemented** migration, produce a **new derived** output with an explicit source/target schema path and retained original package; otherwise do not convert.
- Select a previously owner-approved Studio/Capture build **only by reviewed release manifest, original source SHA, artifact/executable hash, version/build, dependencies and schema compatibility**. Do not substitute an arbitrary old Installer or privately downloaded IPA.
- Before downgrading Capture, export and verify every current package and application state the older version may not understand. An older binary is **not assumed able to read newer projects or schema**.
- Restore from the last independently verified package/library backup if needed. Do not recommend deleting original device sessions, overwriting unbacked libraries or modifying the source package to force compatibility.
- Finally test reinstall, camera permission, offline transfer, project reopening, original data integrity, app build identity and roundtrip on the **real device**. Without executed evidence report **NOT_VALIDATED**, not PASS.

## Safe failure codes for future tooling

`BACKUP_NOT_VERIFIED`, `INVALID_PACKSCAN_CHECKSUM`, `UNSUPPORTED_SCHEMA_VERSION`, `MIGRATION_PATH_NOT_DECLARED`, `APP_SIGNING_NOT_AVAILABLE`, `APPLE_PROVISIONING_EXPIRED`, `BUILD_IDENTITY_UNKNOWN`, `ROLLED_BACK_WITH_UNVERIFIED_DEVICE_STATE`. Do not emit private absolute filesystem paths, owner identifiers, keychain contents, package bytes or scans into logs.

## Remaining real task work after owner lift

Complete code/readiness implementation, confirm application data export and permission semantics against current iOS code, execute controlled physical iPhone test and a full 205-case CI acceptance by an owner-approved **zero-extra-spend** approach, resolve formal license/legal review and security gates, audit PL-0359/0362/0367 independently. This file itself does **not** close any PL task.
