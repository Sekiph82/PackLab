# PackLab Capture: iPhone 16 installation and safe rollback

**Status: installation procedure; physical-device steps have not been executed. Updated 2026-11-04.** This guide documents the current source and hosted build evidence. It is not device acceptance, a signed release, legal approval, or permission to distribute PackLab or its dependencies.

## Current app identity and behavior

| Item | Current source value / evidence |
| --- | --- |
| App display name / bundle ID | PackLab Capture / `com.packlab.capture` |
| Marketing version / build | `0.1.0` / `1` (project defaults, not a released build) |
| Minimum deployment target | iOS 17.0 |
| Hosted build toolchain | macOS 15.8.2; Xcode 16.0 (16A242d); iPhoneOS SDK 18.0; iPhone 16 / iOS 18.0 simulator |
| Camera privacy key | `NSCameraUsageDescription` is present in the current `Info.plist`; physical permission behavior has not been verified |
| Local-network privacy key | `NSLocalNetworkUsageDescription` is absent from the current `Info.plist`; successful physical local-network transfer and its permission prompt are unverified |
| PackScan export | The app has an explicit user-initiated share/export flow for finalized `.packscan` packages. The app does not upload them to a cloud service. |

The values above come from `apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj`, `apps/ios-capture/PackLabCapture/Info.plist`, and the current Swift sources. Confirm the built product’s `Info.plist` and signed identity for every candidate before installing; project defaults alone do not identify an artifact.

## Verified hosted artifacts (unsigned)

PL-0361’s [macOS Capture run 41764141005](https://github.com/Sekiph82/PackLab/actions/runs/41764141005) completed on source commit `f977eb7f3d0a6fee1ff0bd474f5b1557457a590a`. It ran the iPhone 16 / iOS 18.0 simulator XCTest suite: **205 passed, 0 failed, 0 skipped**. It prepared and verified provenance for two unsigned products. The artifacts are temporary CI outputs with one-day retention; check the run’s current Artifacts section before downloading.

| Artifact | Artifact identity and provenance | Valid use |
| --- | --- | --- |
| `packlab-capture-unsigned-simulator-<source-sha>` | Artifact ID `13292221930`; ZIP 2,228,803 bytes, ZIP SHA-256 `912746cab418aadd60fdd452cd45069507dbc2cbf22f4bb67fc6e2c31063bb64`; expires `2026-11-05T03:06:38Z`. JSON sidecar `packlab-capture-simulator-provenance.json`: source `f977eb7f3d0a6fee1ff0bd474f5b1557457a590a`, run `41764141005`, bundle `com.packlab.capture`, simulator product tree 8,178,129 bytes, tree SHA-256 `93639751561f7bff2e338247a160821221ffa3270afa4f7e3f2788d17ba48bde`. | Matching iOS Simulator on macOS only. **Cannot be installed on a physical iPhone.** |
| `packlab-capture-unsigned-device-archive-<source-sha>` | Artifact ID `13291404205`; ZIP 5,380,642 bytes, ZIP SHA-256 `bea54dad45dddd58107a0199e48c065d95f7e3aef090421baf7f4c496dd901d4`; expires `2026-11-05T03:00:07Z`. JSON sidecar `packlab-capture-device-archive-provenance.json`: source `f977eb7f3d0a6fee1ff0bd474f5b1557457a590a`, run `41764141005`, bundle `com.packlab.capture`, unsigned archive product tree 20,800,973 bytes, tree SHA-256 `eb91d6b73ddd8e74163c3168636cb7eafbf9f659994bf385ac383eaec9880fa2`. | Inspect or use as input to a separately authorized signing/export flow. **It is not an installable IPA.** |

The provenance sidecar binds the workflow/source metadata to a deterministic product-tree file count, byte length, and SHA-256. The ZIP digest covers the downloaded Actions artifact archive; the tree digest covers the extracted product. Verify both against the exact run and artifact before use. Artifact IDs and expiration are run-specific, and these files may already be unavailable. If unavailable, use a newly completed, reviewed run and its own sidecar values; never reuse these digests for a different build. Do not upload signing credentials, private scans, or supplier files to public Actions artifacts.

### Simulator installation on macOS

1. Download the simulator artifact from the linked run. Verify the downloaded ZIP byte length and SHA-256, extract it, and run the repository’s provenance verifier from the same source commit. For example, from the PackLab repository root:

   ```sh
   python3 tools/ci/ios_artifact_provenance.py verify \
     --artifact /path/to/PackLabCapture.app \
     --sidecar /path/to/packlab-capture-simulator-provenance.json
   ```

   Do not install if the verifier fails or the sidecar is missing.
2. On a Mac with a compatible Xcode and iOS Simulator runtime, boot an iPhone 16 simulator and obtain its identifier:

   ```sh
   xcrun simctl list devices booted
   ```

3. Confirm the app bundle identity, then install and launch:

   ```sh
   /usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' /path/to/PackLabCapture.app/Info.plist
   /usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' /path/to/PackLabCapture.app/Info.plist
   /usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' /path/to/PackLabCapture.app/Info.plist
   xcrun simctl install <SIMULATOR_UDID> /path/to/PackLabCapture.app
   xcrun simctl launch <SIMULATOR_UDID> com.packlab.capture
   ```

This verifies a simulator build only. It does not establish physical camera, local-network, performance, signing, or distribution behavior.

## Physical iPhone 16 prerequisites

- A Mac with a supported Xcode version and iOS platform support, the PackLab source checkout or a valid signed device artifact, and an iPhone 16 on an iOS version supported by the selected app build. iPhone 16 launched with iOS 18; the app project’s current minimum deployment target is iOS 17.0.
- The owner’s authorized Apple account/team and a signing certificate/profile that matches the app ID and the selected installation route. No Apple ID, device UDID, certificate, profile, private key, or password belongs in this guide, repository, or CI logs.
- A data backup/export completed and verified before removing the existing app. Follow **Back up PackScan data before uninstalling** below before any destructive operation.
- A known source revision and build identity. The hosted artifacts above are unsigned and cannot be installed directly on the phone.

### Connect and trust the device

1. Connect the unlocked iPhone to the Mac with a data-capable cable. In Finder or Xcode, accept **Trust This Computer** on the phone and confirm trust on the Mac. Apple’s [Trust This Computer guidance](https://support.apple.com/en-gb/109054) covers resetting trust if the prompt does not appear.
2. In Xcode, open `apps/ios-capture/PackLabCapture.xcodeproj`, choose the `PackLabCapture` scheme, and select the attached iPhone 16 as the run destination. Sign in through Xcode’s account settings, select the owner-authorized team under Signing & Capabilities, and let Xcode manage development signing only if permitted for that account and app configuration. Apple describes this workflow in [running an app on a simulated or physical device](https://developer.apple.com/documentation/Xcode/running-your-app-on-simulated-or-physical-devices).
3. If iOS requires Developer Mode for this development-signed app, enable it on the phone at **Settings > Privacy & Security > Developer Mode**, restart, confirm the prompt, and enter the device passcode. Apple explains when it appears in [Enabling Developer Mode on a device](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device?changes=_8). Do not weaken other device security settings.

### Route A: local Xcode development install

1. Complete the connection/trust steps above. In Xcode, check the selected team, bundle identifier `com.packlab.capture`, signing status, and iPhone destination. Build and run the selected scheme. Xcode creates or refreshes development signing material when automatic signing is available; this is a development install, not a CI-produced release IPA.
2. Before running, inspect the exact built `.app` selected by Xcode with the three `PlistBuddy` commands in **Simulator installation on macOS** (replace the app path; do not run the `simctl` commands). Record its bundle ID, version/build, source commit, and build/install session in private owner records. Use Xcode Device Hub after installation to confirm the app is present. Do not claim the phone itself verified the installed source SHA or version/build; the current app has no identity readback UI, as described below.
3. If the selected build product’s identity is missing or mismatched, or Xcode reports a signing/profile error, stop before running it. Do not infer identity from project defaults alone.

### Route B: signed IPA (future CI route)

**This route is unavailable in the verified PL-0361 evidence.** That workflow generated an unsigned simulator app and unsigned `.xcarchive`; no signed IPA was produced. PL-0358 remains pending Apple signing credentials. A future CI IPA is usable only after the signing workflow has been explicitly configured and authorized, the produced IPA has a valid signature/profile for this device and intended use, and its own artifact plus provenance have been verified. Never convert or label either unsigned artifact above as a signed IPA.

For a valid registered-device IPA, use the exact signed artifact and its matching provenance. Verify its download digest, signature, embedded provisioning profile, bundle ID, version/build, device eligibility, and expiry before installation. Install through Xcode’s Devices and Simulators window or Apple Configurator as appropriate to the profile and distribution type. Apple’s [registered-device distribution guide](https://developer.apple.com/documentation/xcode/distributing-your-app-to-registered-devices) describes required signing, registered devices, export, and installation; it states that Developer Mode must be enabled each time an IPA-based app is run on an iOS device. If any identity or signature check fails, do not install.

### Optional Personal Team signing

An owner may use a Personal Team for local development signing if Apple and the current Xcode configuration allow this app and device. Apple’s [account overview](https://developer.apple.com/help/account/basics/about-your-developer-account) documents Personal Team limits, including up to 10 App IDs and 3 registered devices, with provisioning expiring after 7 days. Reconfirm current limits in Apple’s account tools before use. Expiry means rebuild/re-sign and reinstall using valid current provisioning; it is not a reason to disable verification or trust an unknown signer. A Personal Team is not App Store/TestFlight distribution approval.

## Permissions and first launch

- **Camera:** The current app declares `NSCameraUsageDescription`. On first camera use, review the iOS permission prompt and allow camera only if the user intends to scan. If access was denied, change PackLab Capture’s camera access in iOS Settings, then retry. Physical camera behavior remains untested.
- **Local network:** The current `Info.plist` does not declare `NSLocalNetworkUsageDescription`, while the source contains a user-initiated URLSession receiver transfer flow. Bonjour discovery was not found in the inspected Capture source. Apple’s [TN3179](https://developer.apple.com/documentation/technotes/tn3179-understanding-local-network-privacy?changes=_9%2C_9) explains local-network privacy prompts and the usage-description key. Do not claim that a prompt or transfer works on iPhone 16. A local-network transfer attempt may fail or lack an explanatory prompt until the app configuration is reviewed and physical behavior tested. Use only a trusted receiver on a network the owner controls; stop on an unexpected host, certificate, or verification error. No cloud transfer service is part of this procedure.
- **Other prompts:** Review any system prompt in context and grant only the permission needed for the intended test. Record sanitized error categories, not private addresses, device identifiers, scans, or secrets.

## Confirm installed build identity

For a local build, inspect the built `.app` before installation. For an IPA, inspect the app under `Payload/PackLabCapture.app` and verify the signature/profile with Apple tooling before install. Confirm:

1. Bundle ID is exactly `com.packlab.capture`.
2. Marketing version and build number match the reviewed artifact; current source defaults are `0.1.0` and `1` only.
3. Source commit and provenance metadata match the selected build.
4. The signature and embedded profile are valid for this device and route (not applicable to the unsigned CI artifacts above, which must not be installed on iPhone).

Use Xcode Device Hub to confirm that `com.packlab.capture` is installed and record the install session, reviewed source SHA, artifact SHA-256, and the version/build read from the exact `.app` or IPA that was installed. **The current Capture app has no About screen or diagnostic flow wired to expose its running bundle version/build or source revision, and Device Hub’s documented Apps panel does not promise to display those fields. Therefore this procedure cannot independently read back the installed version/build/source from the phone.** If exact post-install identity readback is required, record `BUILD_IDENTITY_UNKNOWN` and stop physical acceptance until a verified readback method or in-app build diagnostics exist. Do not infer a physical install from a successful simulator XCTest.

## Upgrade, reinstall, and data preservation

An in-place update normally requires the same bundle ID and an acceptable signing identity/profile. Do not assume data will survive app deletion, team changes, provisioning changes, failed upgrades, or container migration. Confirm the app opens and verify exported packages after each update. If an update fails, stop before deleting the existing app and preserve diagnostic information without private data.

### Back up PackScan data before uninstalling

1. In PackLab Capture, use the app’s share/export action for each finalized `.packscan` session. Choose an owner-controlled destination such as Files or a Mac. The export UI offers a user-selected destination; this is not an automatic cloud backup or a verified device restore mechanism.
2. Copy each export to a separate owner-controlled backup location. Do not attach package contents or scan images to CI, tickets, or the repository.
3. From the PackLab repository root with the locked Python environment available, validate each package against the PackScan container contract, manifest schema, payload sizes, and SHA-256 checksums:

   ```sh
   uv run --locked python -c "from packlab_core.packscan.container import validate_packscan; report = validate_packscan('/path/to/session.packscan'); print('PASS schema=' + str(report.manifest['schema_version']))"
   ```

   A nonzero error means the backup has not passed verification. Retain the original export unchanged and record only sanitized package name/length/hash and validation outcome in private owner records.
4. Confirm every required package has a verified backup and that the owner can locate it. If export, validation, or restore expectations are uncertain, stop. **Do not delete or uninstall the app.**

Only after that gate passes may the owner choose to remove/reinstall if external preservation of the packages is sufficient. Preserve original `.packscan` bytes; never rewrite the manifest, images, timestamps, calibration, or checksums to make a package open. **The current Capture app has no `.packscan` import or restore flow. Exported packages can be preserved externally but cannot currently be restored as in-app sessions. If continuing those sessions inside Capture is required, do not uninstall until an import/restore flow is implemented and tested.**

## Troubleshooting

| Symptom | Safe response |
| --- | --- |
| iPhone does not appear in Xcode | Unlock it, reconnect with a data-capable cable, accept trust prompts on both devices, and check Xcode/Finder again. If the trust prompt cannot be restored, follow Apple’s trust-reset guidance. Do not publish the device serial or UDID. |
| Xcode reports profile, certificate, or signing failure | Check the selected team, bundle ID, certificate validity, profile expiration, and device registration in Xcode/account tools. Refresh or create valid signing assets through the authorized Apple team, then rebuild. Do not reuse a mismatched profile or disable signature checks. |
| Personal Team app stopped launching after expiry | Reconnect to Xcode and rebuild/re-sign with current provisioning, then reinstall. Personal Team provisioning may expire after 7 days; confirm current Apple limits. |
| IPA is rejected or app is missing after install | Recheck artifact digest/provenance, signature, profile, device eligibility, bundle identity, and Developer Mode requirement. Reject stale, unsigned, mismatched, or unverifiable packages. |
| Camera prompt does not appear or camera fails | Check the app’s camera permission in iOS Settings and confirm the expected built `Info.plist` key. Record the OS/app version and sanitized error. Physical camera acceptance remains open. |
| Local-network prompt or transfer fails | Treat this as unverified. The current plist lacks `NSLocalNetworkUsageDescription`; stop rather than assuming a permission or receiver issue. Record a sanitized error and resolve the app configuration before claiming physical transfer support. |
| Existing package cannot be exported or validated | Do not uninstall, overwrite, or mutate it. Preserve the source and seek a verified recovery path; mark `BACKUP_NOT_VERIFIED` or `INVALID_PACKSCAN_CHECKSUM` as applicable. |

## Rollback and compatibility

PL-0367's detailed deterministic procedure and decision matrix are in [`PL0367_ROLLBACK_PLAYBOOK.md`](PL0367_ROLLBACK_PLAYBOOK.md). The current source supports only PackScan `1.0.0` reads/writes and has no migration implementation; unsupported combinations stop explicitly. The original package/project/library remains untouched during rollback, and physical-device behavior remains unverified until actually tested on iPhone.

## Current limitations and external gates

Hosted simulator XCTest passed on runs [41743543561](https://github.com/Sekiph82/PackLab/actions/runs/41743543561) and [41764141005](https://github.com/Sekiph82/PackLab/actions/runs/41764141005); the latter also verified and uploaded the unsigned provenance-bound products listed above. This proves neither a signed iPhone install nor physical camera/local-network behavior. No signed IPA, physical iPhone install, Apple account/device acceptance, legal/license approval, or distribution approval is evidenced here. PL-0358 signing credentials and physical-device validation remain external gates. This guide does not close PL-0367 or authorize M17 work.
