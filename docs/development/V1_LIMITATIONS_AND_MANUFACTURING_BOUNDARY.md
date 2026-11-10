# PackLab V1 limitations and manufacturing boundary

Status: development boundary statement; not a release approval, engineering certification, legal opinion, or manufacturing authorization.

## What PackLab V1 can support

PackLab provides a workflow for capturing package imagery, transferring `.packscan` data, preparing reconstruction inputs, running supported reconstruction stages, reviewing geometry, creating/editing parametric package models, recording label zones/artwork, and exporting software geometry or presentation assets when the corresponding feature/runtime is available.

These functions produce software records and geometry. A successful import, reconstruction, fit, render, CAD export, unit test, desktop build, or hosted build establishes only the property actually checked by that operation.

## Evidence and measurement limits

- **Relative scale:** image-derived geometry may have only relative scale. Pixel, camera-prior, and reconstruction units do not establish physical dimensions.
- **Metric-unverified scale:** a stored millimetre coordinate or CAD export may carry `mm_unverified` authority. It remains unverified until compared against an independent, suitable physical measurement.
- **Physical metrology:** no PackLab software test, public YCB scanner scale, or synthetic tolerance band substitutes for a calibrated measurement plan, traceable reference, uncertainty analysis, repeat captures, and owner acceptance.
- **Capture/reconstruction:** phone imagery and photogrammetry can lose detail on low-texture white HDPE, glossy surfaces, transparent PET, occluded handles, thin walls, sharp edges, internal cavities, and reflective/translucent closures. Warnings and a successful pipeline do not prove missing surfaces are complete.
- **Synthetic data:** Blender-generated dimensions, masks, camera intrinsics/poses, lighting, distortion, shader response, and tolerance bands are simulated software fixtures. They are not physical camera/resin measurements or Kenya field evidence.
- **Public references:** YCB assets retain their own attribution/license terms. A scanned model or photograph is not necessarily a calibrated/registered pair or independently measured physical reference. Third-party trademarks and trade dress are not cleared by dataset licensing.
- **Parametric fit:** software fit metrics apply only to the exact input geometry/revision and chosen algorithm. They do not prove the design matches a production container or meets supplier process tolerances.
- **CAD/render/export:** a valid BREP, STEP round trip, dieline, label overlay, or product render demonstrates software geometry/presentation only. Label print fit, wall thickness, draft, shrinkage, stackability, leakage, strength, chemical compatibility, mold release, and regulatory suitability require separate engineering/physical validation.
- **Recovery/reliability:** deterministic unit or fault-injection tests cover only their simulated failure boundary. Reconstruction orchestration currently does not resume from persisted stage checkpoints; restart/resume from those checkpoints is not demonstrated. Tests do not prove durability on every filesystem, disk, driver, engine build, or power-loss condition.
- **Device and hosted evidence:** simulator/local builds do not prove operation on the owner's iPhone 16. A local workflow does not prove a GitHub Actions artifact exists. Hosted results require a run for the exact committed revision and artifact identity.
- **Kenya operations:** no Kenya factory or Kenya package scan set is available yet. No PackLab benchmark in this repository constitutes Kenya process acceptance.

## Required gates before engineering/production use

Before relying on a model for a package decision, identify and preserve its physical source, acquisition session, parent/revision lineage, calibration/scale authority, independent measurements, uncertainty/tolerance basis, and reviewer/owner decision. Repeat representative scans and measurement comparisons across operators/sessions. Validate materials and product contents with qualified personnel. Validate labels, printing, fit, compliance, and suppliers separately.

## No direct mold manufacture

**PackLab V1 outputs must not be sent directly to manufacture a mold, tooling, production container, closure, or other production part. PackLab does not authorize mold manufacture or production release.** A successful reconstruction, parametric fit, STEP export, render, dataset check, or software test is not a substitute for independently verified physical dimensions, qualified packaging/tooling engineering review, material/process constraints, supplier approval, required regulatory/compliance review, and explicit owner authorization.

If physical accuracy or authority is absent, keep the result labeled relative, unverified, draft, or deferred as appropriate. Do not remove a warning or upgrade authority to make a design appear production-ready.

## Acceptance status

M17 software tests, independent source/security review, hosted artifacts, iPhone capture/transfer, physical package accuracy, and future Kenya operational validation are separate acceptance records. This document does not close those gates or authorize release.
