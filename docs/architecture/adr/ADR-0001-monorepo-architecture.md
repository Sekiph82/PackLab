# ADR-0001 — Use one PackLab monorepo with explicit platform, domain, schema, architecture-documentation, and coordination boundaries

- Status: Accepted
- Date: 2026-09-16
- Decision scope: PackLab repository layout, platform/application ownership, reusable domain boundaries, cross-platform contracts, architecture documentation, public fixtures, and coordination evidence.
- Supersedes: None
- Superseded by: None

## Context / problem

PackLab is a personal packaging digital-twin system whose workflow spans two products and several shared technical boundaries:

- PackLab Capture runs on iPhone/iOS and records packaging captures and supporting metadata.
- PackLab Studio runs on Windows and ingests captures, coordinates reconstruction and measurement, and supports editable design and engineering outputs.

The products evolve together around the .packscan Capture-to-Studio boundary. The repository also needs shared cross-platform contracts, architecture documentation, safe public test fixtures, developer/CI tools, and AI coordination evidence. Without explicit boundaries, a single repository could allow platform UI, domain logic, schemas, generated processing data, and task/audit artifacts to become coupled or be mistaken for one another.

This ADR formalizes the architecture already established by PL-0001 and independently accepted in its audit. It does not invent an unrelated design, and it does not claim that future application directories or runtime implementations already exist.

## Decision

PackLab uses one Git repository with explicit platform, domain, schema, documentation, test, tooling, and coordination boundaries. The planned canonical areas are:

~~~text
apps/ios-capture/
apps/windows-studio/
core/
schemas/
assets/
tests/
tools/
docs/architecture/
coordination/sessions/
~~~

Physical creation of the future apps/ios-capture/, apps/windows-studio/, core/, schemas/, assets/, tests/, and tools/ tree is not part of this ADR task; it remains PL-0019. This record defines ownership only.

The following ownership and dependency decisions are frozen:

- iOS-specific implementation belongs to PackLab Capture: SwiftUI presentation, camera/session integration, capture guidance, device metadata, local scan persistence, PackScan creation, and transfer.
- Windows/PySide6 presentation belongs to PackLab Studio: desktop navigation, workspace/viewport presentation, job controls, ingest UI, and library presentation.
- Reusable Python/domain/application logic remains separate from PySide6 widgets. Studio UI calls PackLab-owned services; domain logic does not require widget types or widget lifecycle.
- Cross-platform machine contracts belong at the future schemas/ boundary. Capture and Studio implement/use the same versioned contract rather than silently forking it.
- Coordination evidence remains separate from product/runtime source under coordination/sessions/. Session prompts, logs, and audits do not become application modules or live task state.
- GitHub main remains repository truth, and root TASKS.md remains live project-state truth. The ADR index and this record do not replace the tracker.
- The Scan Mesh/Scan Master reference chain remains distinct from the editable Design Model. A Design Model may derive from a Scan Master through an explicit fitting/design workflow; editing it must not mutate the Scan Master or source evidence.

External engines and platform libraries remain behind PackLab-owned interfaces and adapters as described by the repository-structure contract. This ADR does not change the established NextLevel, reconstruction-engine, CAD, or Blender boundaries.

## Rationale

One repository lets Capture and Studio evolve in a coordinated way around PackScan while keeping the shared contract visible to both sides. A contract, documentation, fixture, or compatibility change can be reviewed atomically with the affected producer and consumer rather than synchronized manually across unrelated repositories.

The monorepo also provides one auditable architecture and history surface, shared documentation and safe fixtures, and a common home for developer/CI tooling. That is especially useful for PackLab’s single-owner personal-project context, where repository administration and cross-repository release coordination would add overhead without a current organizational benefit.

The decision is not a claim that monorepos are universally superior. Explicit path and layer boundaries preserve independent reasoning and prevent UI/platform coupling even though the files share one repository.

## Alternatives considered

### 1. Separate iOS and Windows repositories

This would isolate platform ownership and could reduce checkout size for each product. It was not selected for the current PackLab context because Capture and Studio must evolve together around PackScan, shared terminology, calibration/pose contracts, and end-to-end evidence. A split would add synchronization and release-coordination work for a single owner. It may be reconsidered if team ownership, access control, or scale changes materially.

### 2. Multiple repositories split by subsystem or core

Splitting domain core, schemas, reconstruction adapters, and products could create independently versioned packages. It was not selected now because the project is at its governance/foundation stage and atomic changes across the contract, core behavior, fixtures, and consumers are more valuable than early package/release overhead. The explicit boundaries in this monorepo preserve the intended separation without prematurely creating multiple versioning and dependency pipelines.

### 3. One repository without explicit ownership boundaries

This would be simple to start, but it would make it unclear whether a widget, engine output, scan, schema, or coordination file is authoritative. It was not selected because PackLab’s central risks include confusing reference scans with editable CAD, coupling domain logic to UI, leaking private assets, and allowing session evidence to become project state. A single repository is useful here only when paired with explicit ownership and dependency rules.

## Consequences / trade-offs

### Positive consequences

- Cross-platform schema and contract changes can be reviewed and released atomically with their Capture and Studio consumers.
- CI, architecture documentation, public fixtures, developer tools, and coordination/audit history have one discoverable repository home.
- Shared terms and ownership rules are easier to reference across the personal project’s workflow.
- Explicit paths make the boundary between platform code, reusable domain behavior, contracts, and evidence reviewable.

### Negative consequences and follow-on work

- The repository can grow as images, meshes, tools, documentation, and both products evolve, increasing clone and navigation cost.
- Unrelated changes can become coupled socially or operationally if ownership is not enforced, even when they are physically separate by path.
- Later work needs clear module ownership, path-scoped CI, and generated-artifact controls so a small documentation change does not trigger every job and private data does not enter public history.
- Public-repository privacy discipline is mandatory for local scans, private Kenya packaging data, confidential supplier files, credentials, and unreleased artwork. Shared location does not make private data publishable.
- A monorepo does not imply that every dependency or runtime must be installed for every subproject. Platform-specific and optional external capabilities should remain discoverable, isolated, and installable only where needed.

## Constraints / invariants

The following audited PL-0001 invariants remain in force:

1. UI is a consumer/presentation layer and must not become domain truth.
2. NextLevel remains behind PackLab-owned capture interfaces; PackLab contracts do not depend directly on NextLevel internals.
3. External engines remain behind PackLab adapters and capability boundaries, with explicit versions, capabilities, inputs, outputs, and failure/provenance behavior.
4. Scan Mesh and Scan Master remain reference/reconstruction representations rather than editable CAD truth.
5. A Design Model may derive from a Scan Master, but editing the Design Model must not mutate the Scan Master or immutable source evidence.
6. Blender and rendered output are presentation/material/UV layers and are not dimensional or engineering source of truth.
7. Private Kenya scans and confidential supplier data stay out of the public source tree unless the owner explicitly approves content as safe public fixture material.
8. Root TASKS.md is the only live project-state tracker; this ADR records no current progress or task queue.

## References / evidence

- ../REPOSITORY_STRUCTURE.md — audited ownership and dependency specification.
- ../GLOSSARY.md — audited PackLab terminology contract.
- coordination/sessions/PL-0001-C001/CHATGPT_AUDIT_V01.md — AUDITED_PASS evidence for the repository-structure architecture.
- coordination/sessions/PL-0002-C001/CHATGPT_AUDIT_V01.md — AUDITED_PASS evidence for the terminology contract.
- TASKS.md — live task authority; it is not replaced by this ADR.
