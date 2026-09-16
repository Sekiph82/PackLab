# PackLab Repository Structure and Ownership

## Purpose and status

This document is the canonical repository-structure specification for PackLab. It defines the intended monorepo boundaries, ownership model, dependency directions, and data mutability rules so that later implementation work has stable architectural constraints.

This is a governance specification, not an implementation of the planned application tree. PL-0001 adds this document only. The physical creation of the future `apps/`, `core/`, `schemas/`, `assets/`, `tests/`, and `tools/` directories is PL-0019 and must not be inferred from this document or from an empty directory appearing in a checkout.

## Planned canonical monorepo map

The following map describes the intended repository areas and their ownership. A path listed here is a planned boundary; it is not evidence that the corresponding application or source files already exist.

```text
apps/
  ios-capture/       iPhone capture product and iOS-specific integration
  windows-studio/    Windows desktop product and PySide6-specific integration
core/                reusable Python/domain/application services
schemas/             versioned cross-platform data contracts
assets/              explicitly approved public fixtures and reusable public assets
tests/               unit, contract, integration, regression, and fixture tests
tools/               developer and CI utilities, diagnostics, and controlled adapters
docs/
  architecture/      architecture specifications and audited decision records
coordination/
  sessions/          immutable, versioned work orders and implementation/audit evidence
```

### Planned area responsibilities

| Area | Planned ownership and contents | Boundary |
| --- | --- | --- |
| `apps/ios-capture/` | PackLab Capture: SwiftUI screens, camera/session orchestration, guided capture, permissions, local persistence, and transfer. | Owns iOS presentation and device integration; it does not own Windows reconstruction or CAD behavior. |
| `apps/windows-studio/` | PackLab Studio: PySide6 windows, navigation, viewport/workspace presentation, job controls, and desktop integration. | Owns desktop presentation and orchestration; it does not redefine domain contracts or external-engine semantics. |
| `core/` | Reusable Python/domain/application services for PackScan handling, calibration, measurements, project data, reconstruction orchestration, fitting, and validation. | Must remain usable without PySide6 widgets and must not contain UI toolkit policy. |
| `schemas/` | Versioned PackScan and project/export contracts, JSON Schemas, coordinate/unit definitions, and public contract fixtures. | Cross-platform contract boundary; changes require compatibility analysis and the repository audit process. |
| `assets/` | Public, redistributable fixtures or explicitly approved sample assets needed by tests, documentation, or examples. | Private scans, confidential supplier files, and unapproved artwork do not belong here. |
| `tests/` | Tests organized by unit, contract, integration, regression, and safe fixture use. | Tests may exercise adapters, but domain tests must not become coupled to a particular UI implementation. |
| `tools/` | Diagnostics, reproducibility helpers, CI utilities, and thin executable-discovery/capability tooling. | Tools support the product and workflow; they do not silently replace the domain or live tracker. |
| `docs/architecture/` | Repository specifications, architecture decision records, and related architectural evidence. | Documents explain or constrain the system; they do not claim unimplemented tasks are complete. |
| `coordination/sessions/` | Versioned prompts, criteria, Codex logs, and independent audit artifacts for a task cycle. | Session artifacts are evidence and work orders, not live project state. |

## Canonical authority and ownership

PackLab has one live project-state authority and a separate evidence trail. The following ownership rules resolve conflicts by assigning each concern to one accountable owner.

| Concern | Authoritative owner | Rule |
| --- | --- | --- |
| Repository contents and shared branch history | GitHub `main` in `Sekiph82/PackLab` | GitHub `main` is repository truth. Local checkouts are working copies and must be synchronized before implementation. |
| Live task, milestone, sprint, actor, and workflow state | Root `TASKS.md` | Root `TASKS.md` is the only live H!veAI/project-state tracker. No document, log, dashboard, or provider-specific file may compete with it. |
| Prompts and frozen audit criteria | ChatGPT | ChatGPT authors versioned work orders and their matching criteria under `coordination/sessions/<CYCLE_ID>/`. |
| Independent audit verdicts and audit artifacts | ChatGPT | ChatGPT independently audits the implementation and writes the matching audit artifact. Codex does not self-audit or assign a verdict. |
| `TASKS.md` lifecycle writes | ChatGPT | ChatGPT is the sole writer of task closure and lifecycle state. Codex must not edit `TASKS.md`. |
| Implementation, test execution, and implementation log | Codex | Codex implements the active work order, runs its required checks, and writes the matching `CODEX_LOG_VNN.md`. Codex does not write audit verdicts or task lifecycle state. |
| Session work orders and evidence | The named author under the coordination protocol | Session artifacts record scope and evidence for a cycle; they do not override live state in `TASKS.md` and do not form a second task ledger. |

The normal authority sequence is therefore: GitHub `main` for repository truth, root `TASKS.md` for live project state, the active versioned prompt and criteria for the current implementation scope, and coordination policy/guidance for the operating rules. Logs and handoff/history files are evidence unless an explicit higher-authority rule says otherwise.

## Application and layer ownership

### PackLab Capture

PackLab Capture is the iPhone product. It owns camera control, high-resolution still capture, capture quality guidance, ARKit/CoreMotion supporting metadata, scan-session persistence, PackScan creation, and transfer/export. It may use SwiftUI and iOS frameworks through PackLab-owned capture services and interfaces.

Capture does not own dense reconstruction, Scan Master promotion, parametric fitting, engineering BREP, STEP export, or Windows UI behavior.

### PackLab Studio

PackLab Studio is the Windows product. It owns ingest, immutable raw preservation, calibration and scale workflows, reconstruction jobs, reconstruction QA, Scan Master promotion, measurement, parametric Design Model editing, engineering export, labels/materials/rendering orchestration, and the packaging library UI.

Studio presentation belongs under `apps/windows-studio/`; reusable Python/domain behavior belongs under `core/`. A PySide6 widget may call PackLab-owned application services, but the service and domain layers must not require a PySide6 widget or event-loop object to perform their work.

### Cross-platform contracts

The `.packscan` container and its manifest, metadata, units, coordinate systems, checksums, versioning, and compatibility rules are owned at the `schemas/` boundary. Capture writes a conforming package; Studio validates and ingests it. Neither product may silently fork the contract in its own UI or device-specific implementation.

PackLab-owned interfaces define the cross-platform meaning of capture data. On iOS, those interfaces may be implemented using AVFoundation or NextLevel, but the domain contract must not depend directly on NextLevel internals. On Windows, external reconstruction and CAD engines are similarly implementation details behind PackLab-owned adapters and capability probes.

## External-engine adapter boundaries

External engines are replaceable capabilities, not owners of PackLab project truth. Each integration must expose explicit discovery, version/capability information, inputs, outputs, provenance, cancellation/failure behavior, and an adapter boundary in PackLab-owned code.

| Engine | PackLab-owned boundary | Responsibility and non-responsibility |
| --- | --- | --- |
| COLMAP | SfM/sparse-reconstruction adapter | Owns camera registration and sparse reconstruction stages. It is not the UI, task tracker, or business-definition source of truth. |
| OpenMVS | Dense-reconstruction adapter | Owns dense cloud, mesh reconstruction, refinement, and texturing stages in the primary reconstruction chain. It does not define editable CAD semantics. |
| Open3D | Point-cloud/mesh analysis adapter | Supports cleanup, registration, normals, components, measurements, decimation, and deviation analysis. Its derived output remains traceable to source evidence. |
| OpenCascade binding | Engineering CAD/BREP adapter | Builds and validates engineering solids from the editable Design Model and supports STEP/CAD operations. It does not promote a triangle scan to engineering truth. |
| Blender | UV/material/render adapter | Consumes approved geometry, artwork, and material data for repeatable visual presentation. Render output is never the dimensional or engineering source of truth. |

External command syntax, executable paths, and installed versions must stay behind these boundaries. Core and UI code should depend on PackLab adapter capabilities and normalized result records rather than on undocumented engine-specific side effects.

## Dependency direction rules

The intended dependency flow is inward toward PackLab-owned contracts and domain/application services, with platform and third-party details at the edges:

```text
SwiftUI / iOS UI  ->  PackLab Capture services  ->  PackScan schemas
PySide6 UI        ->  PackLab application services  ->  Python/domain core
                                                        |
                                                        +-> external-engine adapters
                                                        +-> project/data contracts
```

The following rules are mandatory for future work:

1. UI code may depend on PackLab-owned domain/application services. Domain and application logic must not depend on PySide6 widgets, widget lifetimes, or UI-only state.
2. Swift capture UI may depend on PackLab-owned capture services. PackLab capture/domain contracts must not depend directly on NextLevel internals; NextLevel belongs behind an iOS camera-service boundary.
3. External engines are accessed through PackLab-owned adapters and capability probes. Business logic must not scatter raw COLMAP, OpenMVS, Open3D, OpenCascade, or Blender command assumptions across the UI.
4. Reconstruction and scan artifacts are evidence or derived geometry. They do not become CAD truth automatically merely because an engine produced a mesh or a successful-looking result.
5. A Design Model may derive from a Scan Master through an explicit fitting/promoting workflow. A Scan Master must not depend on the Design Model, so the reference cannot be changed implicitly by an edit to the design.
6. Rendering may consume Design Model, material, and artwork data. Rendering must not become the engineering source of truth, and a rendered appearance must not be used as proof of dimensional correctness.

Later tasks may refine module placement and interfaces through audited architecture decision records. They must not silently invert these ownership or dependency boundaries.

## Geometry and data ownership

PackLab distinguishes source evidence, reconstruction products, editable design data, and presentation/export outputs. Provenance should travel forward whenever a derived artifact is created.

| Data class | Examples | Mutability and ownership |
| --- | --- | --- |
| Immutable/protected source evidence | Original capture photos, imported `.packscan` bytes, capture metadata, checksums, and raw ingest copies | Preserve unchanged after ingest. Corrections create a new revision or derived record rather than silently rewriting source evidence. |
| Regenerable derived reconstruction data | COLMAP databases/results, sparse points, OpenMVS dense clouds/meshes/textures, Open3D cleanup products, masks, QA metrics, and temporary stage outputs | Regenerable from protected inputs and recorded settings. Safe to invalidate or replace when the source or processing configuration changes. |
| Promoted reference data | Scan Master, its scale/calibration provenance, normalization decisions, and measurement results | A distinct, reviewable reference derived from reconstruction evidence. It remains separate from both raw intermediates and editable design geometry. |
| Editable project/design data | Project metadata, fitting parameters, profiles, cross-sections, symmetry constraints, feature definitions, Design Model revisions, Label Zones, and material assignments | User-editable and versioned. Changes must not mutate the original capture or Scan Master. |
| Engineering/export artifacts | Validated BREP solids, STEP/STL/OBJ/GLB exports, technical drawings, dielines, and export manifests | Generated from a stated project/design revision. They are outputs with provenance, not a replacement for the Design Model or source evidence. |
| Private/local-only data | Local scan collections, reconstruction workspaces, Python environments/caches, Xcode/Swift build products, Blender temporary output, private Kenya scans, confidential supplier drawings/quotes, and unapproved proprietary artwork | Keep outside public Git or under an explicit later ignore/access policy. Do not add these as fixtures by accident. |
| Safe public fixtures | Synthetic data, public-domain or redistributable samples, minimal contract fixtures, and explicitly approved documentation assets | May be committed only when provenance, redistribution permission, and suitability for public CI/documentation are clear. |

### Scan Mesh, Scan Master, and Design Model

The raw reconstruction and any resulting triangle Scan Mesh are reference evidence, not editable engineering solids. A Scan Master is a deliberately promoted and normalized reference scan with a traceable link to its capture, reconstruction stages, scale, and QA evidence. It is still distinct from a Design Model.

The Design Model is a separate, parameter-driven and editable representation of package geometry. It may use profiles, cross-sections, dimensions, symmetry, closure references, handles, and constrained features. It is not created by relabeling or overwriting a triangle Scan Mesh. An OpenCascade BREP or STEP artifact is an engineering representation derived from the validated Design Model, not an alias for the scan mesh.

Artwork, Label Zones, textures, and PBR material assignments are also separate from engineering body geometry. One physical Design Model may therefore support multiple artwork/SKU presentations without duplicating or altering the underlying package geometry.

## Generated, runtime, and private locations

The following categories must remain outside Git by default. Their exact ignore patterns, cache policy, and backup policy belong to later audited source-control and environment tasks; this document does not implement PL-0021 or those tasks.

| Category | Examples of local-only location/content | Rule |
| --- | --- | --- |
| Local scan data | A user data directory such as `%LOCALAPPDATA%\\PackLab\\scans\\` or a separately managed local storage volume | Raw photos and `.packscan` packages are protected evidence and must not enter the public repository. |
| Reconstruction intermediates | A per-project workspace such as `%LOCALAPPDATA%\\PackLab\\work\\` | COLMAP/OpenMVS/Open3D databases, dense outputs, logs, and retry scratch data are regenerable and local-only unless a fixture is explicitly approved. |
| Python environments and caches | `.venv/`, virtual-environment directories, package caches, model caches, and tool downloads | Never commit environments, mutable caches, credentials, or unknown downloaded binaries. |
| Xcode/Swift build products | `DerivedData/`, `.build/`, device archives, simulator products, and signing outputs | Build products are generated and local/CI artifacts, not source. Signing material remains secret. |
| Blender temporary output | Temporary `.blend` files, render scratch directories, intermediate image/texture output, and cache folders | Keep temporary presentation output local; commit only explicitly approved reproducible assets or documentation output. |
| Private Kenya/supplier assets | Private product scans, supplier drawings, quotes, unreleased artwork, and other confidential material | Local/private unless the owner explicitly approves a safe, redistributable fixture. |

When a generated artifact is intentionally published, it must be placed in a clearly documented, reproducible output path and have an explicit provenance/retention decision. A later audited policy may define the corresponding `.gitignore` and CI artifact rules.

## Naming and future-structure constraints

These principles stabilize references without prematurely implementing the separate source-control-conventions task (PL-0007):

- Use the permanent `PL-xxxx` task ID and cycle/version identifiers in coordination evidence names, such as `PL-0001-C001/CODEX_LOG_V01.md`.
- Prefer descriptive lowercase directory names with hyphens where a directory name is needed, matching the planned paths in this specification.
- Keep cross-platform contract names and schema versions explicit; do not hide breaking changes behind a filename-only rename.
- Give immutable captures, Scan Masters, Design Models, and exports distinct identifiers or revision markers so their provenance cannot be confused.
- Name generated workspaces by project/revision/stage when they must be inspected, and keep them outside the public source tree by default.
- Keep public fixtures visibly separate from private production data and record redistribution provenance for any fixture that is committed.

Future structure changes may add modules or refine boundaries only through the repository’s audited governance/ADR process. No later task may silently invert ownership, merge Scan Mesh with Design Model, make a presentation layer the source of dimensional truth, or turn a session artifact into a competing live tracker.

## Scope guard for PL-0001

PL-0001 establishes this specification only. It does not create the planned application/core/schema/assets/tests/tools tree, implement PackLab Capture or Studio, add external-engine integrations, establish source-control ignore rules, or complete any future task. Those changes require their own authorized task and audit evidence.
