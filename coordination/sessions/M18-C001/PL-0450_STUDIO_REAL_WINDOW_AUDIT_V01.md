# PL-0450 Studio real-window audit V01

- Source: `origin/main` @ `ee760a9618ed50fc72d50c7deefd3bb97b5ceefc` (open PRs #10 receiver/viewer, #11 engines and #12 build-model are NOT merged, so they are not audited here)
- Harness (outside the repo): `C:\Users\sekip\Documents\PackLab-work\studio_audit_pl0450.py`
- Command: `QT_QPA_PLATFORM=offscreen QT_QPA_FONTDIR=C:\Windows\Fonts uv run python C:\Users\sekip\Documents\PackLab-work\studio_audit_pl0450.py` -> exit 0, 0 uncaught exceptions
- Raw log: `C:\Users\sekip\Documents\PackLab-work\studio-audit\audit_log.json`; screenshots in the same folder (`A-*` = no project, i.e. what a fresh launch shows; `B-*` = project created through the `StudioMainWindow.new_project()` API, because there is no UI for it)
- Window: the same `StudioMainWindow()` constructor `app.run()` uses. The only change is that the library and diagnostics roots are redirected to a temp dir so owner AppData stays untouched. No providers are injected, matching production.
- Method: routes are selected by mouse-clicking the real `packlab.navigation.routes` list. Buttons are pressed with `QTest.mouseClick`. Text is read from `widget.text()`.
- Limitation: offscreen Qt only. This is not the frozen PackLab.exe, and the real desktop was not used.

## What the window contains (measured)

- Menu bar: **no actions**. Toolbars: **none**. There is no New/Open/Close Project, Import, or File menu anywhere.
- Routes: Library, Capture Inbox, Reconstruction, Editor, Mask Correction, Exports, Settings.
  - Without a project, clicking Capture Inbox, Reconstruction, Editor and Exports does nothing (the items are disabled, and `nav_reached=false`).
- Docks: Scene / Objects, Properties / Inspector and Logs are placeholder `QLabel`s that show only their own title. Jobs / Activity is a real `JobPanel`, but it is empty.
- Capture Inbox view (`navigation.CaptureInboxView`): one label, "Capture Inbox", with no buttons. Production passes `ingest_controller=None, receiver=None`.
- Reconstruction view: a bare `QLabel("Reconstruction")`.
- Inconsistency: the Mask Correction nav item stays enabled without a project, but `RouteStack.set_project_available` disables its view. The result is a greyed-out page that can be reached by clicking.

## Feature table

Legend: W = works in window, B = broken (exception), C = not reachable (service exists, no UI path), D = reachable only with a project/source the UI cannot create.

| # | Feature | PL IDs | Code entry point | UI path tried | Result | Screenshot |
|---|---|---|---|---|---|---|
| 1 | Shell, navigation, docks | 0135-0137 | `shell.StudioMainWindow`, `navigation.NavigationPanel`, `workspace.WorkspaceManager` | launch, click every route | W (4 of 7 routes disabled until a project exists; 3 docks are title-only placeholders) | A-noproject-library.png |
| 2 | Window preferences | 0138 | `preferences.PreferencesStore` | n/a. Production passes `preferences=None` | C (no store is constructed in `app.run`, so geometry and route are never persisted) | - |
| 3 | Jobs panel / cancel / safe shutdown | 0139-0140 | `jobs.JobPanel`, `shutdown.ShutdownCoordinator` | Jobs dock visible | W but empty (nothing in the window ever submits a job) | A-noproject-library.png |
| 4 | Diagnostic bundle | 0141 | `StudioMainWindow.create_diagnostic_bundle` | searched menus/buttons | C | - |
| 5 | About/version screen | 0142 | `version.AboutView` | Settings route | W (version 0.1.0, PySide6 6.11.2, schema 1.0.0, build revision "unknown") | A-noproject-settings.png |
| 6 | New/Open/Close project | 0143-0145 | `project.ProjectManager.new_project/open_project/close` | searched menus/buttons | C (API only. Every project-gated route is therefore unreachable for the owner) | A-noproject-capture-inbox.png |
| 7 | Autosave, history, recovery, invalidation, portability | 0146-0150 | `autosave.AutosaveService`, `history.HistoryManager`, `StudioMainWindow.accept_recovery`, `ProjectManager.portability_report` | n/a | C (no UI: no recovery prompt, no undo, no portability report) | - |
| 8 | 3D viewport (load, orbit, grid, mm cues, selection, debug modes, screenshot, LOD) | 0151-0157 | `viewport.ViewportService`, `QtRasterViewportAdapter`, `viewport_export.export_viewport_preview` | no viewer route on main | C (used only inside the library asset-detail preview, which needs an asset the UI cannot create, see #28. Viewer is in unmerged PR #10) | B-api-project-library.png |
| 9 | Ingest / file import / iPhone receiver | M05 feeding M06 | `ingest.IngestController`, `receiver.PackLabReceiver` | Capture Inbox route | C (no project: route disabled. With API project: label only, no buttons) | B-api-project-capture-inbox.png |
| 10 | Engine discovery / config | 0158-0162 | `engine_config.discover_engines` | Settings | C | A-noproject-settings.png |
| 11 | Reconstruction (one-click COLMAP+OpenMVS, cancel, QA, confidence) | 0163-0183, 0192-0201 | `reconstruction_execution.ReconstructionExecutionService`, `pre_reconstruction_qa.build_packscan_pre_reconstruction_qa`, `photo_duplicates.build_packscan_photo_duplicate_report` | Reconstruction route | C (view is a bare QLabel with the text Reconstruction) | B-api-project-reconstruction.png |
| 12 | Segmentation (SAM 2.1), postprocess, mask lifting (object-only) | 0184-0187, 0189-0191 | `packlab_core.sam21_backend`, `mask_postprocessing.post_process_mask`, `object_mask_lifting`, `mask_review.build_mask_review_bundle` | none | C | - |
| 13 | Manual mask correction | 0188 | `mask_correction.MaskCorrectionView.begin` | Mask Correction route; clicked Undo/Submit/Cancel | D (view is reachable, but all buttons are disabled with "Open a mask correction session to begin." Nothing in the window calls `begin` with a `MaskArtifact`) | B-api-project-mask-correction.png |
| 14 | Marker scale, axes, base plane, upright, front direction, normalization | 0202-0209 | `calibration.scale_estimation`, `base_plane.detect_base_plane_candidates`, `upright_alignment.compute_upright_alignment`, `normalization_transform.compose_normalization_transform`, `ProjectManager.persist_front_direction/persist_scale_provenance` | none | C | - |
| 15 | Measurements in mm (bbox, 2-point, diameter, sections, profile, neck, capacity, uncertainty, report) | 0210-0218 | `bounding_dimensions.measure_bounding_dimensions`, `two_point_measurement.measure_two_point_distance`, `cross_section_measurement.measure_cross_section`, `measurement_report.build_measurement_report` | none | C | - |
| 16 | Mesh processing (cleanup, normals, smoothing, holes, decimation, stats) | 0225-0232 | `component_cleanup.cleanup_isolated_components`, `mesh_smoothing.smooth_triangle_mesh`, `hole_filling.fill_reported_mesh_holes`, `proxy_decimation` | none | C | - |
| 17 | Promote to Scan Master | 0233, 0238-0239 | `shell._promote_scan_master_from_editor` -> `ScanMasterPromotionAction.promote` | Editor route, filled Actor/Reason, clicked Promote | D (without a project the route is disabled. With an API project the click returns "No eligible captured cleanup selection is loaded." because `scan_master_request_provider=None` in production) | B-api-project-editor-after-promote.png |
| 18 | Repeat-scan registration, heatmap, section overlay, revision switching | 0234-0237 | `repeat_scan_registration`, `scan_design_heatmap.compute_scan_design_heatmap`, `cross_section_overlay`, `design_review.ScanDesignReviewWidget` | none | C (`ScanDesignReviewWidget` is never instantiated) | - |
| 19 | Scan Master export PLY/OBJ/GLB | 0240 | `ProjectManager.export_selected_scan_master` via `EngineeringExportView` | Exports, source "Scan Mesh / Scan Master" | D ("No selected persisted Scan Master revision is available.", Export disabled) | B-api-project-exports-src0.png |
| 20 | Parametric Design Model: fitting, zones, dimension edit, control points, presets | 0241-0260 | `revolved_design_model.build_axisymmetric_revolved_design_model`, `design_profile_fit.fit_design_profile`, `design_dimensions.revise_overall_dimension`, `design_control_point_edits` | none | C (no Design Model view or parameter editor) | - |
| 21 | Caps/closures, jerrycan, trigger/pump, tube/sachet families | 0261-0288 | `closure_workflow.ClosureWorkflowController`, jerrycan/trigger_pump/tube/pouch modules | none | C (`ClosureWorkflowController` is never instantiated) | - |
| 22 | CAD export STEP / STL / OBJ+GLB + manifest + round-trip | 0289-0302 | `engineering_export.EngineeringExportView.export_selected` -> `export_design_model_step/stl/obj_glb` | Exports, source "Editable Design Model / CAD" | D ("No active Design Model source is connected...", formats None, Export disabled. `design_model_export_source_provider=None` in production) | B-api-project-exports-src1.png |
| 23 | Technical drawing / dimension sheet SVG, DXF, PDF | 0303-0309 | `technical_drawing_export.export_technical_drawing_vectors`, `technical_drawing_pdf` | Exports formats list | C (only `build_smoke` calls it. Not an export format in the UI) | B-api-project-exports-src1.png |
| 24 | Label zone, placement, artwork import, wrap, dieline SVG | 0310-0317 | `label_zone_placement.create_label_zone_placement_revision`, `label_artwork.ingest_label_artwork/map_label_artwork_to_zone`, `label_dieline_svg.export_label_dieline_svg` | none | C | - |
| 25 | Materials and PBR assignment | 0318-0323 | `starter_material_catalog.create_starter_packaging_material_catalog`, `component_material_project.create_component_material_project` | none | C | - |
| 26 | Blender mockup render / GLB | 0324-0331 | `blender_render.render_standard_views`, `blender_glb_export` | none | C | - |
| 27 | Packaging library browse/search/filter | 0339-0343 | `packaging_library_browser.PackagingLibraryBrowserView.refresh` | Library, clicked Refresh and Clear filters | W, but always empty ("No packaging assets in this library.") | A-noproject-library-after-clicks.png |
| 28 | Create asset / link scan/Scan Master/Design Model/artwork | 0332-0338 | `PackagingLibraryAuditStore.create_asset/link_source/create_relationship` | none | C (there is no New-asset UI, so the library can never be populated from the window) | - |
| 29 | Create SKU from existing geometry | 0344 | `PackagingLibraryBrowserView._create_sku` -> `CreatePackagingSkuDialog` | clicked "Create SKU from selected geometry" | D ("Select a packaging asset before creating a SKU." No asset can exist, see #28) | A-noproject-library-after-clicks.png |
| 30 | Library backup/restore, contact sheet | 0345-0346 | `packaging_library_backup.PackagingLibraryBackupService`, `packaging_library_contact_sheet.PackagingLibraryContactSheetExporter` | none | C | - |

No feature was **B** (broken). Clicking produced 0 uncaught exceptions. Everything that is not W is C or D.

## Minimal wiring needed (owner flow order)

1. **Project lifecycle (#6, prerequisite for all D items).** Add a File menu to `StudioMainWindow` with New/Open/Close that calls the existing `new_project/open_project/close_project` methods, plus a folder picker. Also construct `PreferencesStore` in `app.run` (#2) and add a Help menu item "Create diagnostic bundle" that calls `create_diagnostic_bundle` (#4).
2. **Imported scan (#9).** Pass a real `IngestController` and `PackLabReceiver` into `StudioMainWindow` from `app.run`, and give `CaptureInboxView` Import/Receive buttons. Unmerged PR #10 does this; on import, create or open a project.
3. **3D model (#11, #8).** Add a Build-model button to the Reconstruction route that calls `ReconstructionExecutionService` through `ProjectManager.create_reconstruction_workspace` + `JobManager`, and show the pre-reconstruction QA report first. Replace the placeholder QLabel with a `ViewportService`/`QtRasterViewportAdapter` viewer. PRs #10 and #12 cover this partly.
4. **Object-only (#12, #13, #16).** After reconstruction, run `sam21_backend`, then `mask_postprocessing.post_process_mask`, then `object_mask_lifting`, then `component_cleanup.cleanup_isolated_components`. Feed a selected frame mask into `MaskCorrectionView.begin`. Implement `scan_master_request_provider` in `app.run` from that cleanup result so Editor > Promote works (#17), which in turn enables Scan Master export (#19).
5. **Scale/measure in mm (#14, #15).** Add a Measure panel (the Properties dock is an empty placeholder today) that calls `calibration.scale_estimation` + `ProjectManager.persist_scale_provenance`, `upright_alignment`/`base_plane`/`normalization_transform`, then `measure_bounding_dimensions`, `measure_cross_section` and `measure_two_point_distance`, with an export button calling `build_measurement_report`.
6. **Editable Design Model (#20).** Add a Design route: "Fit from Scan Master" calls `fit_design_profile` + `build_axisymmetric_revolved_design_model`, then H/W/D spin boxes call `design_dimensions.revise_overall_dimension`, with a preview via `cad_preview` in the viewer. Comparison uses `design_review.ScanDesignReviewWidget` (#18).
7. **Labels (#24-#26).** In the same route, add a Labels tab: `create_label_zone_placement_revision`, Import artwork (`ingest_label_artwork` + `map_label_artwork_to_zone`), Export dieline SVG (`export_label_dieline_svg`), a material picker from `create_starter_packaging_material_catalog`, and Render mockup (`blender_render.render_standard_views` as a job).
8. **Factory export (#22, #23).** Supply `design_model_export_source_provider` in `app.run` that returns the active Design Model + BREP + preview from step 6; STEP/STL then work through the existing `EngineeringExportView`. Add a "Dimension sheet (SVG/DXF/PDF)" format calling `export_technical_drawing_vectors`/`technical_drawing_pdf`.
9. **Library population (#28, #30).** Add "Add to library" from the project, calling `PackagingLibraryAuditStore.create_asset` + `link_source`, and Backup/Contact-sheet buttons calling the existing services.
10. Small fix: include `Route.MASK_CORRECTION` in `NavigationPanel.set_project_available` so the nav gating matches the view gating.

## Verdict

**4 W (shell/nav, jobs dock, About, library browse which is always empty), 0 B, 21 C, 5 D.** None of the owner-flow steps (import, model, object-only, measure, Design Model, labels, factory export) can be operated from the window on main @ ee760a96. Each C/D item should become a wiring task before new feature work. PL-0441..0449 already cover most of them. Items #2, #4, #6, #7, #10, #21, #28, #30 and the nav-gating fix have no M20 task yet.

This is an offscreen audit of the source runtime, not the frozen PackLab.exe on the owner desktop. Physical/factory accuracy is out of scope.
