# Test evidence: real-device .packscan (PL-0439, PL-0385) V01

- Tester: Claude test specialist (non-implementing). Date: 2026-11-22.
- Validator source: `Sekiph82/PackLab` main HEAD `185c2dbfdf1fa85384fc38f1592fe7fecd04263e` (`core/src/packlab_core/packscan/container.py::validate_packscan`).
- Interpreter: repo `.venv` Python run with `-I` (isolated); `core/src` inserted on `sys.path` inside the script, as `-I` ignores `PYTHONPATH`.
- Inputs: owner-private and read-only. Nothing was copied into Git and no image content is included here. Paths are relative to the Studio `transfer-inbox` and project directories under `%LOCALAPPDATA%\PackLab\PackLab Studio`.
- Modifications: none. The file sha256 and mtime were identical before and after validation.

## Observations

| Check | Command / method | Expected | Observed | Result |
|---|---|---|---|---|
| Integrity | sha256 of `raw/88c745b4…e48a.packscan` (37,259,301 B) | equals file name | equal | PASS |
| ZIP central directory | `zipfile.ZipFile(...).testzip()` | `None`, readable | `None`; 43 entries; first entry `manifest.json` | PASS |
| Unmodified validation | `validate_packscan(raw file)` | no `PackScanError` | accepted; script exit code 0; 41 payloads | PASS |
| Manifest | read from the validated report | schema-valid required fields | schema 1.0.0; created_at 2026-11-22T10:53:35Z; device iOS iPhone17,3 (an iPhone 16 model), os 27.2.1; capture_mode freehand v1; capture_id 24B7F9E8…; source_evidence original_capture / immutable / packlab_ios_capture | PASS |
| Payload kinds | count `manifest.payloads[].kind` | all in schema enum | image 20 (.heic), other 20 (.json), photo_metadata 1; all are in the `manifest.schema.json` enum | PASS |
| Ingest report | `reports/88c745b4….json` | network channel, no repair | source_channel `network`; image_count 20; package_sha256 matches; no "repair" anywhere; warnings: calibration_owner_required plus 3 optional-missing (mask, diagnostics, calibration) | PASS |
| Transfer record | `transfers/81488F70….json` | complete, digest verified | state complete; expected = actual sha256; bytes 37,259,301/37,259,301 | PASS |
| Windows import into project | `projects/default/raw/captures/88c745b4….packscan` | same digest | sha256 identical | PASS |
| Build from this capture | `working/reconstruction/r-0aec7a06…/manifest.json` | references this package | source_digest 88c745b4…; state `succeeded`; 20 input images whose sha256 set equals the manifest image payloads; COLMAP/OpenMVS outputs present | PASS |
| Downstream Scan Master | `derived/scan_master/42367d8e…/manifest.json` | traceable to the build | raw_capture_sha256 23680c41… equals the sha256 of the reconstruction output `mvs/scene_textured.obj`; scale_state metric-unverified; physical_accuracy DEFERRED_OWNER_VALIDATION; mold_use_authorized false | PASS (traceability only) |

## Per-task verdict

- **PL-0439**: a fresh real-device export was validated unmodified on Windows. Its central directory parses, the manifest is schema-valid with created_at/device/capture_mode/source_evidence, all payload kinds are in the enum, and there was no manual repair. **PASS**
- **PL-0385**: an iPhone 16 (iPhone17,3) .packscan was delivered over the network to the real Studio receiver, verified by digest, imported into the project, and reconstruction succeeded. **PASS** for the end-to-end iPhone -> .packscan -> Windows import criterion.

## Limitations

- The app build (d85cbcde) is not recorded in the package manifest, so this evidence cannot confirm it. It rests on the owner's report.
- QR pairing was not observed directly. The only evidence for it is the network channel and the completed transfer record.
- None of this shows physical dimensional accuracy. Scale is metric-unverified and calibration is owner_required.
- Under the same transfer-inbox, `ingest-index.json` lists only an earlier package (c5d78a55…), not 88c745b4…. Bookkeeping should be checked separately. This does not affect either verdict.
