# PL-0357 Codex Peer Review V01

**Reviewed source SHA:** `b94e73744544feae7f5dddcdbfbef22c2cab392d`
**Verdict:** PASS for the unsigned generic iOS archive task.

## Source and workflow review

- The archive is a distinct `capture-unsigned-device-archive` job with no dependency on the simulator/XCTest job and no signing-secret context. Workflow/job permissions are read-only `contents`.
- Pull requests and `main` pushes already include the iOS app/project and this workflow in path filters. The archive job uses pinned checkout, cache, and artifact-upload actions.
- It resolves the committed NextLevel 0.19.1 lock and applies only the existing narrow runner-local Swift 5 compatibility change before running `xcodebuild archive` for `generic/platform=iOS`.
- Archive build uses `CODE_SIGNING_ALLOWED=NO`, `CODE_SIGNING_REQUIRED=NO`, and empty identity. Validation checks exact app executable name, bundle/version/build/iPhoneOS metadata, rejects any provisioning profile or `_CodeSignature`, and requires `codesign` to report the executable is not signed.
- Provenance records source SHA, run ID, runner/macOS/Xcode/iPhoneOS SDK, generic destination, app metadata, unsigned settings, lock digest, and that no IPA was produced.
- Upload scope is limited to the `.xcarchive` and its plain-text manifest, pinned action, one-day retention, and fail-closed missing-file behavior. No IPA export occurs.
- PL-0356 simulator/XCTest job remains unchanged by this task.

## Hosted evidence

- Archive job in [run 41754385597](https://github.com/Sekiph82/PackLab/actions/runs/41754385597), job `126326942762`, passed on exact reviewed SHA `b94e73744544feae7f5dddcdbfbef22c2cab392d`. The overall run concluded `success`.
- The hosted run passed generic archive creation, unsigned profile/signature checks, provenance creation, and upload. The codesign output is captured and not printed; successful validation confirms the expected unsigned diagnostic was observed.
- Artifact API reported `packlab-capture-unsigned-device-archive-b94e73744544feae7f5dddcdbfbef22c2cab392d`, ID `13287651642`, 5,380,516 bytes, expiry `2026-11-05T01:31:32Z`.
- Downloaded artifact inspection found seven files / 20,800,973 logical archive bytes, no embedded provisioning profile, no `_CodeSignature` directory, and no IPA. The archived app reports `com.packlab.capture`, Capture 0.1.0/build 1, `iphoneos`, SDK `iphoneos18.0`, and supported platform `iPhoneOS`. Provenance matches the run/SHA and SDK/Xcode values.
- Separate simulator regression job in the same run passed all 205 XCTest cases: `Passed`, 205/205, zero failed, zero skipped.

## Independent reviews and scope limits

- Workflow/source reviewer: PASS; no actionable findings. Recommended exact executable basename validation, which was implemented and re-reviewed.
- Tester: PASS for hosted unsigned archive and artifact; after completion, confirmed the full workflow and 205-case simulator regression suite are green.
- Security/provenance reviewer: PASS; no secrets, profiles, certificates, keychains, private data, or material provenance defect found.
- This artifact is an unsigned CI archive and is not a directly installable IPA. No device installation, signing, release, legal, or physical acceptance is claimed.
