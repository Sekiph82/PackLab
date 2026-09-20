# PackLab

PackLab is a GitHub-first monorepo for turning packaging captures into traceable, editable digital-twin work. The product separates source evidence, reconstructed reference geometry, and editable design truth so that a visual scan is never silently treated as an engineering solid.

## Product flow

```text
iPhone Capture -> PackScan -> Windows Studio -> reconstruction -> Scan Master -> editable Design Model
     SwiftUI        contract       PySide6             planned             promoted reference       planned
```

PackLab Capture is intended for a non-LiDAR iPhone 16 Standard baseline. PackLab Studio is Windows-first and will coordinate ingest, reconstruction, QA, measurement, and design workflows as later milestones implement them. The GitHub Actions macOS boundary is reserved for future iOS builds and tests; this Windows checkout does not claim native Xcode or device evidence.

The Scan Mesh/Scan Master is reference evidence with provenance. The Design Model is a separate parameter-driven, editable representation. A mesh, render, or exported file does not replace either source evidence or the Design Model.

## Architecture

```text
SwiftUI/iOS UI  ->  PackLab Capture services  ->  schemas/PackScan contracts
PySide6/Windows UI  ->  packlab_core services  ->  adapters and external engines
                                             ->  project data and validation
```

Third-party engines remain replaceable capabilities behind PackLab-owned boundaries. Core logic stays importable without PySide6, and platform presentation does not own cross-platform contracts.

## Repository map

| Area | Ownership |
| --- | --- |
| `apps/ios-capture/` | SwiftUI Capture presentation and iOS/device integration |
| `apps/windows-studio/` | Windows Studio presentation and desktop integration |
| `core/` | Reusable Python/domain/application services |
| `schemas/` | Versioned cross-platform contracts and fixtures |
| `assets/` | Approved public-safe assets only |
| `tests/` | Unit, contract, integration, regression, and safe fixture tests |
| `tools/` | Diagnostics, reproducibility, and thin developer/CI utilities |
| `docs/architecture/` | Architecture specifications and ADRs |
| `docs/development/` | Developer policies and workflow guidance |
| `coordination/sessions/` | Versioned prompts, criteria, logs, and audits; not live status |

The full ownership specification is [`REPOSITORY_STRUCTURE.md`](docs/architecture/REPOSITORY_STRUCTURE.md).

## Current developer quick-start

This M01 foundation is intentionally incremental. On a supported Windows development checkout:

1. Clone the repository and open a PowerShell terminal at its root.
2. Read [`TASKS.md`](TASKS.md) for the current authorized task and [`AGENTS.md`](AGENTS.md) for execution boundaries.
3. Use the documented Python version and bootstrap instructions once the M01 tooling files are present.
4. Run the focused Python tests and checks described in [`docs/development/TESTING.md`](docs/development/TESTING.md) when those M01 files are available.

The iOS project is source-controlled for later macOS/Xcode validation; Xcode, simulator, physical-device, signing, reconstruction engines, and production PackScan behavior are not claimed by this README as available on Windows today.

## Governance and reference material

- [Canonical task state](TASKS.md)
- [Agent instructions](AGENTS.md)
- [Architecture and repository structure](docs/architecture/REPOSITORY_STRUCTURE.md)
- [Monorepo ADR](docs/architecture/adr/ADR-0001-monorepo-architecture.md)
- [Supported host/device baseline](docs/architecture/SUPPORTED_HOST_DEVICE_BASELINE.md)
- [Versioning policy](docs/architecture/VERSIONING_POLICY.md)
- [Dependency and license register](docs/architecture/DEPENDENCY_LICENSE_REGISTER.md)
- [Secrets policy](docs/security/SECRETS_POLICY.md)
- [Audit policy](coordination/AUDIT_POLICY.md)

Private scans, supplier material, credentials, signing identities, and unsupported accuracy claims do not belong in this public repository.
