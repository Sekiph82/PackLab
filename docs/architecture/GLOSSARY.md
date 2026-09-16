# PackLab Glossary

## Purpose and precedence

This glossary defines PackLab-specific terminology for the Capture-to-Studio workflow, reconstruction/reference chain, editable packaging geometry, engineering exchange, and visual packaging outputs. It is terminology guidance, not an implementation of schemas, source code, CAD logic, capture behavior, or reconstruction behavior.

Ownership and dependency boundaries are specified in [`REPOSITORY_STRUCTURE.md`](REPOSITORY_STRUCTURE.md). Where a term becomes a machine-validated contract, the normative definition belongs in a versioned contract under the future `schemas/` area. This glossary does not override root `TASKS.md`, the active session scope, normative schemas, or audited architecture decision records.

## Products, contracts, and representations

### PackLab Capture

PackLab Capture is the iPhone product responsible for controlled high-resolution still capture, capture-quality guidance, camera metadata, supporting ARKit/CoreMotion metadata, scan-session persistence, and creation/transfer of `.packscan` packages. It creates or records source evidence and capture metadata; those inputs are protected after ingest. Capture is not PackLab Studio, a dense reconstruction engine, or a CAD editor.

### PackLab Studio

PackLab Studio is the Windows product that ingests `.packscan` data, preserves the raw source, runs calibration and reconstruction workflows, promotes Scan Masters, measures and fits Design Models, and coordinates engineering, label, material, rendering, and library workflows. Its PySide6 UI presents and orchestrates PackLab-owned application services; reusable domain logic is not owned by the widgets. Studio does not silently rewrite Capture evidence.

### PackScan / `.packscan`

PackScan is PackLab’s versioned Capture-to-Studio interchange/container concept. A `.packscan` package carries the capture evidence and associated metadata needed for safe ingest, such as images and applicable camera, pose, calibration, quality, and integrity information. Capture produces it and Studio validates/ingests it across the product boundary. The exact archive layout, manifest fields, checksum rules, and compatibility behavior are future schema work beginning with PL-0044 and are intentionally not frozen by this glossary. A PackScan is not a Scan Mesh, Scan Master, Design Model, or certified measurement result.

### Source Evidence / Raw Capture

Source Evidence, also called Raw Capture in PackLab, is the protected original record of a capture and ingest: original photographs, the imported `.packscan` bytes, capture metadata, and integrity information. Capture creates the initial evidence and Studio preserves an immutable raw-ingest copy. It is the input to later processing and is not a cleaned mesh, Design Model, or presentation render. Corrections create a new revision or derived record rather than silently mutating the evidence.

### Reconstruction Intermediate

A Reconstruction Intermediate is a derived, usually regenerable processing result or scratch-stage record between source evidence and a promoted reference, such as COLMAP databases, registered cameras, sparse points, OpenMVS dense outputs, temporary meshes/textures, masks, or QA metrics. PackLab reconstruction adapters and analysis services create these artifacts from stated inputs and settings. They may be invalidated and regenerated; they must not be mistaken for the immutable source, the reviewed Scan Master, or engineering CAD truth.

### Scan Mesh

A Scan Mesh is triangle/reference geometry produced by reconstruction or mesh processing from capture evidence. It is owned by the reconstruction/reference workflow, is derived and generally regenerable, and can support inspection, measurements, or fitting. A Scan Mesh is not an editable parameter-driven Design Model and is not editable engineering/CAD truth. It must not be confused with a Scan Master, a BREP solid, or a rendered product asset.

### Scan Master

A Scan Master is a deliberately promoted and normalized reference scan derived from reconstruction evidence after applicable QA, scale, coordinate, and provenance decisions. PackLab Studio promotes it as a stable reference revision distinct from raw reconstruction intermediates and from the Design Model. It may be used to measure, compare, or fit editable geometry, but it remains reference data rather than engineering CAD. A new normalization or correction produces a traceable revision; editing a Design Model must never mutate the Scan Master.

### Design Model

A Design Model is PackLab’s separate, editable, parameter-driven representation of packaging geometry. It is created or fitted by PackLab geometry services from dimensions, profiles, cross-sections, features, constraints, and—where appropriate—a Scan Master. It owns user design revisions and may regenerate preview meshes or engineering BREP outputs. It must not be a relabeled triangle Scan Mesh, must not overwrite source evidence, and must not alter the Scan Master when edited.

### Digital Twin

In PackLab, a Digital Twin is the governed relationship for a packaging asset and its revisions—not merely a pretty 3D mesh and not necessarily one file. Depending on what has been captured and approved, it can link asset identity and metadata to source evidence, a promoted Scan Master, one or more editable Design Model revisions, engineering exports, compatible components, Label Zones, artwork, material assignments, and provenance. Optional layers may be absent; a twin can begin with an identity record and source evidence and gain representations over time. Asset identity is distinct from each representation and revision, and none of those representations alone is automatically the whole Digital Twin.

## Geometry and engineering terms

### Parametric Geometry

Parametric Geometry is geometry generated from named parameters, relationships, constraints, and construction rules that can be edited and regenerated. In PackLab it belongs to the Design Model layer and can express package dimensions, profiles, symmetry, closures, handles, and other controlled features. It may be fitted against a Scan Master but is not the Scan Mesh itself. A visually similar mesh without editable parameters is not Parametric Geometry.

### Profile

A Profile is an ordered two-dimensional outline used by PackLab geometry services to describe a package section through a dimensioned plane, commonly a bottle or jar height-versus-radius/width outline for a revolve or loft. It is editable Design Model input with units and reference axes, and it may be fitted from Scan Master evidence. A Profile is not a complete 3D scan, a cross-section perimeter at an arbitrary plane, or a label Dieline.

### Cross-Section

A Cross-Section is a planar slice or perimeter representation of package geometry at a defined position and orientation, such as a measured body section used for lofting a non-circular container. In PackLab it is Design Model construction data or a derived fitting observation with coordinate and unit context. Multiple cross-sections may generate Parametric Geometry; one is not by itself a complete Scan Master, mesh, or artwork boundary.

### Feature / Parametric Feature

A Feature is a named, meaningful geometric detail or region of a package; a Parametric Feature is that detail represented by editable parameters and constraints. PackLab examples include a neck, shoulder transition, closure seat, handle opening, grip indentation, crimp, or symmetry constraint. Features belong to the Design Model or its fitting metadata and may reference Scan Master evidence. They are not arbitrary mesh triangles, textures, or a license to bake an untracked edit into the source scan.

### BREP / B-Rep

BREP, or boundary representation (B-Rep), is PackLab’s engineering geometric/topological representation layer for validated surfaces and solids, accessed through the OpenCascade/CAD boundary. It is derived from a Design Model and can support topology validation and engineering operations before export. BREP is not a triangle Scan Mesh, not the Scan Master, and not the interchange file format called STEP. A BREP result does not retroactively make reconstruction output engineering truth.

### STEP

STEP is the engineering interchange/export format used by PackLab to exchange validated Design Model/BREP geometry with compatible CAD systems. PackLab generates it from an identified Design Model revision through the CAD boundary and records applicable export provenance. A STEP file is an output artifact, not the conceptual source-of-truth Design Model and not a synonym for BREP, Scan Mesh, or Digital Twin.

## Reconstruction, camera, and metric terms

### SfM — Structure from Motion

SfM is the sparse reconstruction concept in which PackLab estimates relationships among overlapping images, including camera relationships/poses and sparse scene structure. COLMAP is the planned PackLab SfM/sparse adapter boundary. SfM output is derived from source evidence and settings; it is not dense surface geometry, a Design Model, engineering CAD truth, or proof of certified metric accuracy by itself.

### MVS — Multi-View Stereo

MVS is the dense reconstruction concept in which PackLab uses calibrated or posed multi-view imagery to estimate denser surface/point geometry. OpenMVS is the planned primary dense MVS adapter boundary for dense cloud, mesh, refinement, and texturing stages. MVS output remains derived reconstruction evidence and does not by itself establish engineering CAD truth or certified metric accuracy. MVS is not the same conceptual stage as SfM, even though both consume overlapping imagery.

### Camera Intrinsics

Camera Intrinsics are the camera-and-lens parameters used by PackLab to interpret image measurements, such as focal lengths, principal point, distortion, and the reference image dimensions/resolution. Capture records available device metadata and calibration services may refine a profile for a device/lens/resolution. Intrinsics are camera-internal parameters; they are not the camera’s position/orientation (extrinsics/pose), object scale, or a guarantee that a reconstruction is metrically certified.

### Camera Extrinsics / Pose

Camera Extrinsics, or Pose, describe where a camera is and how it is oriented relative to a declared PackLab coordinate system at a capture or reconstruction time. ARKit/CoreMotion may provide supporting metadata and SfM may estimate poses; the reconstruction adapter owns the normalized processing result. Pose is camera-to-world or world-to-camera information according to the explicit contract, not intrinsic lens calibration, a mesh, or a guarantee of absolute scale.

### Calibration

Calibration is the PackLab process of estimating or validating camera, marker, scale, coordinate, or related measurement parameters from known references and recorded conditions. Capture may record device context; Studio/core calibration services apply and assess the relevant profile or marker observations. Calibration produces evidence and confidence/uncertainty context, but a calibration pass does not promise certified metrology, eliminate reconstruction limitations, or turn a Scan Mesh into CAD truth.

### Scale / Metric Scale

Scale, or Metric Scale, is the documented mapping that places PackLab reconstruction/reference coordinates into real-world engineering units, with millimetres as the intended canonical unit where applicable. It is established or checked from calibration evidence, known marker geometry, supplied dimensions, or another recorded reference and belongs in provenance. Scale is not the same as visual size or camera pose, and the presence of a scale factor alone does not prove certified dimensional accuracy.

### Coordinate System

A Coordinate System is the explicit PackLab definition of axes, origin, handedness, orientation, units, and transforms used to relate images, poses, scans, Design Models, components, and exports. The PackScan/schema boundary and downstream services must state which coordinate system applies when data crosses a boundary. It is not merely the current viewport orientation and cannot be inferred safely from a pretty render. A coordinate system also does not supply metric scale unless scale evidence is separately present.

## Labels, materials, assets, and evidence

### Label Zone

A Label Zone is a geometric placement and usable-region concept associated with packaging geometry, such as the front, back, or wrap area where artwork may be applied. PackLab Studio or design services define or suggest it on a Design Model and retain its placement, curvature, margins, and related metadata separately from body geometry. A Label Zone is not the artwork image, not the 2D Dieline, and not permission to change engineering dimensions.

### Dieline

A Dieline is a two-dimensional, dimensioned boundary or template defined or derived for label/artwork production use. In PackLab it can be generated from an approved Label Zone and geometry or supplied as controlled design data, with units, bleed, and safe-margin context where applicable. It is not a 3D Scan Mesh, the physical package body, or the artwork itself; a Dieline must not silently redefine the Design Model.

### Artwork

Artwork is the visual content—such as label graphics, logos, copy, colors, or imagery—that PackLab maps to a Label Zone or Dieline for a SKU or presentation. It is a separate visual/design asset and may vary across multiple SKUs using one physical Design Model. Artwork remains separate from engineering body geometry; it does not own or edit that geometry, replace a Dieline, or provide evidence of dimensions or material properties.

### Material Assignment / PBR Material

A Material Assignment links a component or surface of a PackLab Design Model/render scene to an appearance description. A PBR Material is a physically based rendering description such as base color, roughness, transmission/opacity, IOR, and supported normal detail. Studio/material services and Blender’s render adapter consume these assignments for product description and visualization. They are presentation/product-description data, not engineering geometry, certified material specification, or authority to redefine dimensions.

### Packaging Asset

A Packaging Asset is the governed library identity for a physical or intended packaging item or family, with fields such as internal ID, package family, nominal volume, supplier/material metadata, and provenance status. It is owned by the PackLab asset/library domain and can link multiple source captures, one or more Scan Master revisions, Design Model revisions, compatible components, and SKU artwork. It is not a single mesh, export, label image, or Digital Twin representation; factual supplier fields and PackLab estimates must remain distinguishable.

### Component / Assembly

A Component is a separately identified reusable packaging part or subassembly, such as a bottle body, jar, cap, closure, trigger, pump, dip tube, or handle feature. An Assembly is the governed relationship, transforms, references, and compatibility information that combines components for a package configuration. PackLab uses this boundary to reuse a closure or trigger/pump across assets without duplicating body geometry. A component/assembly is not automatically a single fused mesh, a Scan Master, or a replacement for the Design Model’s feature and mating references.

### Provenance

Provenance is the traceable record of where a PackLab asset or representation came from and how it was produced or changed. It may include source capture/package identity, checksums, device/lens context, calibration and scale evidence, coordinate system, engine versions/settings, processing stages, source revisions, Design Model revisions, operator decisions, and export details. Provenance is carried from protected evidence through derived Scan Masters, Design Models, BREP/STEP exports, and presentations as applicable. It explains lineage and confidence; it is not a second task tracker or an audit verdict.

### Fixture / Public Test Fixture

A Fixture is a controlled input or expected-output sample used to validate PackLab behavior. A Public Test Fixture is limited to synthetic, public-domain, or explicitly redistributable content whose provenance and license permit repository/CI use. It may exercise schemas, adapters, or geometry logic without containing private production evidence. A fixture is not a private Kenya scan, confidential supplier asset, unreleased artwork, or a substitute for physical/device acceptance evidence.

## Relationship summary

The intended conceptual chain is:

```text
PackLab Capture -> PackScan -> Source Evidence
                               -> reconstruction intermediates
                               -> Scan Mesh -> Scan Master -> Design Model
                                                               -> BREP -> STEP
                                                               -> Label Zone / Dieline / Artwork
                                                               -> Material Assignment / render
```

This chain is not a promise that every Digital Twin has every layer. Each transition must preserve ownership, mutability, units, coordinate context, and provenance, and the resulting representation must not be mistaken for another layer merely because it looks similar.
