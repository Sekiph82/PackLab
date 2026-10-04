# ADR-0005 — Standalone Design Geometry Root Authority

Status: **ACCEPTED**  
Date: 2026-10-04  
Scope: PackLab Design Model parent authority for model-only package design

## Context

The accepted M11 Design Model contract was intentionally scan-bound: every `DesignModelRevision` pins one exact Scan Master through `DesignModelParentBindingRevision`.

M12 introduces package families such as tubes and sachets that must also support deliberate model-only creation from user-authored or reference dimensions. Creating a placeholder Scan Master would falsely claim captured ancestry. Requiring a real Scan Master for all model-only work would prevent legitimate design-first workflows.

## Decision

PackLab supports **two explicit parent-authority modes** for parametric design.

### 1. CAPTURED_SCAN_MASTER

This is the existing accepted path.

- exact Scan Master revision/digest required;
- existing `DesignModelParentBindingRevision` semantics remain;
- captured lineage and scale provenance remain exact;
- existing revision IDs and canonical scan-bound serialization must remain backward compatible.

### 2. STANDALONE_DESIGN_GEOMETRY

This is a new explicit model-only root authority.

It is **not** a Scan Master, reconstruction, RAW_CAPTURE, OBJECT_CAPTURE_GEOMETRY or captured evidence.

A standalone root must be immutable and versioned and must contain at minimum:

- project ID;
- root revision ID and deterministic content digest;
- authority class exactly equivalent to `STANDALONE_DESIGN_GEOMETRY`;
- source kind, such as `USER_AUTHORED_NOMINAL_DIMENSIONS`, `REFERENCE_DIMENSIONS`, or reviewed reusable template/preset;
- coordinate unit and unit provenance;
- actor/process, reason and timestamp provenance;
- `physical_accuracy_validation_status=DEFERRED_OWNER_VALIDATION`;
- `mold_use_authorized=false`;
- explicit statement that no Scan Master/captured ancestry exists.

No fake or sentinel Scan Master revision ID, geometry digest, reconstruction revision or captured scale-provenance ID may be invented for this path.

## Unit semantics

Standalone model-only dimensions may use:

- `reconstruction_units` with RELATIVE state where explicitly intended; or
- `mm_unverified` with METRIC_UNVERIFIED state for nominal/reference design dimensions.

`mm_unverified` is a design unit, not evidence that a physical object was measured or validated. PL-0220 through PL-0224 remain deferred and standalone design does not satisfy them.

## Shared Design Model contract

The implementation may generalize the Design Model parent contract with a discriminated parent-authority representation or another equally explicit backward-compatible design.

Mandatory invariants:

1. existing scan-bound Design Model behavior remains valid;
2. existing accepted scan-bound revision identities and canonical serialization must not silently change;
3. standalone revisions must not populate scan-specific fields with fabricated values;
4. generic Design Model editing/history/validation/serialization/preview may support both parent kinds;
5. captured-only comparison/fitting/deviation services must explicitly reject standalone parents when captured evidence is required;
6. standalone-to-scan binding, if supported later, is an explicit new revision/rebind operation and never silent retargeting;
7. Scan Master can never be synthesized from standalone design geometry;
8. M13 CAD/BREP/STEP authority is unaffected and remains separate.

A versioned serialization contract extension is permitted for standalone documents if required, provided existing scan-bound documents remain readable and stable.

## Consequences

Model-only tube/sachet/package design can proceed truthfully without fake scan ancestry. Captured fitting continues to use exact Scan Master bindings. Downstream code must branch on explicit parent authority rather than assuming all Design Models are scan-derived.

Physical validation and mold/manufacturing authorization remain outside this ADR.
