# PL-0367 | Capture, Studio, and PackScan Rollback Playbook

## Status and authority

This is a deterministic operator procedure, not a release approval or a claim that any signed/released rollback artifact exists. Use `docs/architecture/VERSIONING_POLICY.md` and the exact source/build declarations in a verified release manifest. `StudioVersion`, `CaptureVersion`, and `PackScanSchemaVersion` are independent. Never decide compatibility by comparing their numbers or by assuming an older app can open newer data.

Current source declares Studio `0.1.0`, Capture `0.1.0` build `1`, and PackScan schema `1.0.0`. The PackScan container and release-manifest generator support only schema `1.0.0` for reads/writes; `migrations` must be empty. There is no PackScan migration implementation and no production release manifest. Current hosted iOS products are unsigned simulator/archive outputs; they do not include an installable signed IPA. Consequently, the procedure below defines the safe decision path, while an actual application rollback remains blocked until an exact reviewed manifest/artifact pair and applicable signing/device acceptance exist.

## Deterministic compatibility decision

First verify the candidate artifact, its release manifest, and the independent review evidence that applies to that exact source/manifest. A manifest must bind the exact source commit, the independent application/schema versions, platform, build identity, dependency/toolchain identity, artifact digest/length, and the PackScan compatibility declaration. The `packscan_compatibility` record binds a digest-checked policy reference; it does not contain a general-purpose capability list. Verify the artifact against its provenance receipt. The release-manifest generator is preparation-only and does not prove independent review. The PL-0366 checklist validates only an exact clean current-source candidate; it cannot replace the historical review evidence belonging to a prior rollback artifact. Preparation-only manifests, builder logs, version strings without manifest evidence, stale artifacts, and expired/unavailable artifacts do not select a rollback target.

| Decision input | Deterministic result |
| --- | --- |
| Exact release manifest, provenance receipt, or artifact is missing, stale, digest-mismatched, or not independently accepted for the intended use | `STOP / ROLLBACK_TARGET_UNVERIFIED`; do not install it. |
| Observed package schema is inside the selected manifest's declared inclusive `read_min`–`read_max` range, and the bound compatibility-policy evidence covers any optional fields/enum values encountered | `READ_SUPPORTED` for that exact artifact only; open a verified copy first. |
| Package schema is outside the declared range and the selected manifest has no exact, implemented, independently reviewed `source_schema -> target_schema` migration path | `STOP / UNSUPPORTED_PACKSCAN_SCHEMA`; do not ingest, rewrite, or downgrade the data. |
| A future release declares an exact migration path and the matching migration implementation has its own verified compatibility evidence | Migrate a copy to a new derived package; preserve and retain the original bytes and digest. If the implementation, source/target pair, or evidence does not match exactly, stop. |
| App downgrade is requested but the previous artifact's manifest and bound compatibility-policy evidence do not explicitly support the package schema/features | `STOP / DOWNGRADE_UNSUPPORTED`; keep the existing app/data intact or use a supported forward version. |

The current validator rejects a read range other than exactly `1.0.0` and rejects every non-empty migration claim. Therefore the only current declared schema match is `1.0.0` with `read_min = read_max = write = 1.0.0`; this does not imply that an older Studio or Capture build can read it without that build's own verified manifest declaration.

## Select the prior application build

1. Identify the last known-good Studio or Capture build by its independently reviewed release manifest. Record its application version, Capture numeric build where applicable, exact source commit, platform, artifact SHA-256 and byte length, workflow/provenance reference, dependency/toolchain identity, and schema read/write declaration.
2. Confirm the artifact is still available and its bytes match the receipt. Do not reconstruct it from a commit, choose the nearest semantic version, reuse a simulator app as an iPhone build, or use a historical installer/IPA with different provenance.
3. Confirm the selected artifact's manifest declares the package schema range and its digest-bound compatibility-policy evidence covers the needed features. For Studio, also confirm the relevant project/library format and required runtime dependencies. If any declaration is absent or ambiguous, stop with `ROLLBACK_TARGET_UNVERIFIED`.
4. Do not assume a rollback of the application also rolls back project data, library metadata, package schemas, or migrations. Keep application selection and data recovery as separate decisions.

## Preserve projects, libraries, and `.packscan` evidence

Before replacing, uninstalling, or downgrading an application:

1. Keep the source project, library, and original `.packscan` packages in place. Make a byte-preserving owner-controlled copy of the complete project directory and every referenced external asset; verify file-tree hashes and open only the copy. There is no current project-specific versioned backup/restore contract. For Packaging Library data, use `PackagingLibraryBackupService.create_backup`, validate the archive with `validate_backup`, and restore only into a new/empty destination. The service rejects unsafe archives and does not silently overwrite a populated destination. Verify the restored audit chain and attachment digests before using that copy.
2. In Capture, export each finalized `.packscan` using the app's explicit share/export flow. Copy it to a separate owner-controlled backup location and run the existing `validate_packscan` check against that copy from the PackLab repository root:

   ```sh
   uv run --locked python -c "from packlab_core.packscan.container import validate_packscan; report = validate_packscan('/path/to/owner-copy.packscan'); print('PASS schema=' + str(report.manifest['schema_version']))"
   ```

   Retain the original package bytes and SHA-256 in private owner records. A validation failure means the backup is not verified; do not uninstall Capture.
3. Capture currently has no in-app `.packscan` import/restore flow. Exported packages can be preserved and validated externally but cannot presently be restored as Capture sessions. If session continuity inside Capture is required, stop before uninstalling or clearing app data.
4. Never edit `manifest.json`, image bytes, timestamps, calibration, source metadata, or checksums in the original package to make it compatible. A supported migration, if implemented in the future, must read a copy and emit a separate derived package with a new identity and explicit loss/limitations.

## Apply the rollback

### PackLab Studio on Windows

1. Preserve the current project and Packaging Library backups first. Keep their original locations untouched.
2. Verify the selected Windows installer/executable digest and manifest. Check the exact Studio version, source commit, Python, Qt/PySide6, OCP/OCCT, Open3D, and other declared runtime dependencies against that artifact's build identity. Dependency license/notice information is a separate release gate; a version match is not legal clearance.
3. Install only the exact reviewed artifact. Open a duplicate of the project/library backup first; do not allow an older build to rewrite the only copy. If the project format, library state, or PackScan schema is unsupported, stop and retain diagnostic codes and hashes without private data.
4. Confirm the running build identity against the manifest, then verify project opening, library audit state, attachment hashes, and read-only access to original `.packscan` evidence. Do not claim acceptance from a successful installer or process launch alone.

### PackLab Capture on iPhone

Use the companion [iPhone 16 installation/reinstallation procedure](PL0362_PL0367_OFFLINE_INSTALL_ROLLBACK_PREPARATION.md) for device trust, installation routes, signing distinctions, and exact current app identity. Its hosted unsigned simulator and archive artifacts are not installable on iPhone.

1. Do not install the current unsigned simulator app or unsigned device archive on an iPhone. Require an independently verified signed IPA (or a separately authorized Xcode development-signed build), matching bundle ID, provisioning route, source/build provenance, and device eligibility.
2. Verify exported `.packscan` backups before any app removal. An in-place update generally requires the same bundle ID and an acceptable signing identity; do not assume data survives deletion, team changes, or container migration.
3. Preserve the currently installed app until the owner chooses a supported install/recovery route and the data backup is independently confirmed. If reinstall is necessary, install only the exact reviewed artifact and follow the matching source-version installation instructions.
4. Verify bundle ID `com.packlab.capture`, Capture marketing version, numeric build, source commit, artifact digest, and signature/profile from the exact installed `.app`/IPA. The current app has no trusted in-app running-build/source readback. If exact installed identity cannot be read back, record `BUILD_IDENTITY_UNKNOWN` and stop physical acceptance.
5. Test only against copies first: launch, camera flow, export, package validation, and required local-network behavior. Physical camera, network transfer, and reinstall/restore behavior remain `NOT_VALIDATED` until exercised on the real device. Do not claim device acceptance from simulator XCTest.

## Stop, recover, and record

Stop before destructive action when backup verification fails, manifest/artifact identity is missing, the schema is unsupported, downgrade compatibility is undeclared, a migration is unavailable, signature/build identity is unverifiable, or app data cannot be restored. Keep original files untouched. Private `.packscan` names and hashes belong only in private owner records. Repository evidence may record sanitized versions, public source/build artifact or manifest digests, schema value, and one of the stable decision codes above; never place private scan hashes, supplier files, device IDs, signing credentials, or absolute owner paths in repository evidence.

No signed IPA, production manifest, exact prior rollback artifact, physical iPhone acceptance, or in-app Capture restore path is established by this playbook. It does not authorize a public release, Git tag, PL-0368, or M17 acceptance.
