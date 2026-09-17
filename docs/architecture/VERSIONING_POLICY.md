# PackLab Versioning Policy

## Status and scope

This document defines the semantic-versioning and compatibility policy for the
three independently versioned PackLab public contracts. It is a policy
artifact, not a release manifest and not a declaration that any example
version has shipped. Release numbering, manifests, tags, and release
automation belong to later authorized work, including PL-0363 and PL-0364.

The policy applies to:

- **StudioVersion** — the public version of PackLab Studio;
- **CaptureVersion** — the public version of PackLab Capture; and
- **PackScanSchemaVersion** — the version of the serialized `.packscan`
  contract.

These domains are related because Studio and Capture exchange `.packscan`
packages, but they are **not numerically locked to each other**. A Studio
release, Capture release, and schema release may advance independently when
their own public contract changes.

This policy does not create application source, schema files, manifests,
release tooling, tags, or releases.

## 1. Version domains and notation

Studio and Capture use SemVer-style `MAJOR.MINOR.PATCH` versions:

```text
StudioVersion: 0.1.0
CaptureVersion: 0.1.0
```

PackScan uses an explicit semantic schema version with the same three numeric
components:

```text
PackScanSchemaVersion: 1.0.0
```

The numeric examples above are illustrative examples only, unless a later
authorized release decision explicitly freezes them. They must not be read as
claims that a production release already exists or has already shipped.

The three names are distinct version domains. A change to one domain does not
automatically require a corresponding numeric change to either other domain.
Each future implementation must state which domain changed and why.

## 2. Studio and Capture SemVer rules

For StudioVersion and CaptureVersion, a version has the form
`MAJOR.MINOR.PATCH` with an optional prerelease identifier and optional build
metadata as permitted by the chosen SemVer implementation. The compatibility
meaning is:

- **MAJOR** increments for an incompatible public behavior, API, persisted
  project-format, or runtime-contract change. Existing supported consumers
  must not be expected to continue working without an explicit migration,
  compatibility layer, or other declared support.
- **MINOR** increments for a backward-compatible public feature, tool,
  capability, or other additive behavior. Existing supported consumers and
  workflows retain their intended compatibility.
- **PATCH** increments for a backward-compatible bug fix or correction that
  does not intentionally change a public compatibility contract.

Internal refactoring, code cleanup, or implementation replacement alone does
not require a MAJOR increment when the public behavior, API, persisted
project format, and runtime contract remain compatible. The impact on public
contracts, not the size of the internal change, determines the bump.

Prerelease identifiers are allowed for internal or test releases. Examples
include `0.1.0-alpha.1`, `0.1.0-beta.1`, and `0.1.0-rc.1`. A prerelease is
still subject to the same explicit compatibility declarations appropriate to
its intended consumers.

Versions in the `0.y.z` range identify development-stage software. This
development-stage convention does **not** waive PackLab's explicit
compatibility, migration, immutability, unit, coordinate-system, or diagnostic
requirements. A `0.y.z` consumer must not guess compatibility merely because
the MAJOR component is zero.

## 3. PackScan schema bump rules

PackScanSchemaVersion governs the meaning and structure of serialized
`.packscan` packages. The schema version must describe both structural and
semantic compatibility; it is not merely a file-format label.

### Schema MAJOR

Increment MAJOR for an incompatible structural or semantic change where an
older compliant reader cannot safely interpret the new package without
explicit migration or newly implemented support. Examples include:

- removing or incompatibly renaming a required field;
- changing the semantic meaning of a required field or file;
- changing canonical units or changing a unit interpretation;
- changing coordinate-system conventions or frame meaning;
- changing checksum interpretation in a way that breaks older readers; or
- changing required photo-orientation or calibration semantics so an older
  compliant reader would interpret evidence incorrectly.

### Schema MINOR

Increment MINOR for a backward-compatible additive change. New optional
fields, optional files, and optional enum values are permitted only when the
schema contract says older readers can safely ignore them or handle them
without misinterpreting the package. Optional enum/value evolution must be
conservative: a value is not a safe MINOR addition if an older reader could
mistake it for a known value or otherwise process it incorrectly. A reader
must have an explicit rule for unknown optional values before treating the
addition as compatible.

### Schema PATCH

Increment PATCH for a compatibility-preserving correction or clarification
that does not change valid serialized meaning or required reader/writer
behavior. A documentation-only clarification may use a schema PATCH when it
clarifies an existing serialized meaning or required behavior that was already
true. It may use no schema bump when it changes documentation wording only,
without changing or clarifying the serialized contract. Not every textual
schema edit requires a version bump.

A PATCH bump must never silently:

- add, remove, rename, or change a required field;
- change required units or their interpretation;
- change coordinate conventions or frame meaning;
- change checksum semantics;
- change photo orientation or calibration meaning; or
- change the meaning of a required file.

If a proposed correction changes any of those things, it is not a PATCH even
if the serialized syntax looks similar; classify it under the applicable
MAJOR rule and provide migration/support as required.

## 4. Compatibility matrix policy

Compatibility is a declared capability, not an inference from application
recency or from a numerically close version. Future Studio and Capture builds
must perform explicit schema-version and capability checks before reading,
writing, or migrating a package. The following matrix is the expected policy
baseline; an individual release may support a narrower range, which it must
declare.

| Situation | Required behavior |
| --- | --- |
| Older Studio reads a newer PackScan schema | Proceed only if the older Studio explicitly supports that schema version and its additive/optional contract. Otherwise reject cleanly with a diagnostic; do not guess. |
| Newer Studio reads an older PackScan schema | Accept directly only for a declared supported older major/minor/patch range, or run an explicit supported migration that produces a derived representation. Preserve the original input. |
| Older Capture writes schema consumed by newer Studio | Newer Studio should accept it when its declared reader range supports the emitted schema, including a supported migration path where applicable. The newer reader must not require newer fields merely because it is newer. |
| Newer Capture writes schema consumed by older Studio | This is compatible only when Capture explicitly targets a schema version and feature set supported by that older Studio. If it emits an unsupported newer schema, the older Studio must reject it cleanly rather than reinterpret it. |
| Future schema MAJOR is unsupported | Reject cleanly and report the encountered version, supported range/capabilities, and required upgrade or migration action. |
| Older schema MAJOR is supported with a migration path | Identify the exact source and target versions, validate the path, create a new derived representation, and retain the original `.packscan` evidence unchanged. |
| Same MAJOR with higher MINOR | Accept only when the change is within the declared additive/optional compatibility contract and the reader can safely handle every encountered addition. Otherwise reject or migrate explicitly. |
| Same MAJOR and MINOR with higher PATCH | Accept only when the release declaration and schema contract confirm that serialized meaning and required behavior remain compatible. Never use PATCH proximity as permission to reinterpret data. |

This matrix does not promise universal forward compatibility or universal
backward compatibility. In particular, a newer writer may emit a package an
older reader cannot use, and a newer reader may not support every older
major. Unsupported, incomplete, malformed, or future packages must produce a
clear diagnostic rather than a best-effort guess.

## 5. Reader and writer behavior contract

### Reader contract

A future PackScan reader must:

1. Read and validate the package's explicit schema version before interpreting
   version-dependent content.
2. Reject an unsupported future MAJOR cleanly.
3. Accept a same-MAJOR newer MINOR only when the additive/optional rules are
   preserved and the reader explicitly supports the relevant capabilities.
4. Accept PATCH differences within a supported MAJOR/MINOR only when the
   declared semantics remain compatible.
5. Never silently reinterpret units, coordinate frames, checksum rules, photo
   orientation, calibration meaning, or required file semantics.
6. Surface clear diagnostics for unsupported, incomplete, malformed, or
   future versions, including the encountered version and the relevant
   supported capability or migration information where available.
7. Preserve immutable raw input during import, compatibility handling, and
   migration. Reading must not rewrite the original `.packscan` evidence.

Millimetres remain PackLab's canonical engineering units unless a future
audited ADR explicitly changes that contract. Coordinate-system semantics must
remain explicit and versioned; a reader cannot infer a frame from a model,
photo order, filename, or application version.

A future PackScan writer must:

1. Emit exactly one explicit PackScanSchemaVersion for each package.
2. Emit no field or file whose required behavior exceeds the declared schema
   version.
3. Validate that optional additions and enum values obey the declared reader
   compatibility contract.
4. Keep deterministic output and checksum-generation implementation for the
   later PackScan schema tasks; this policy does not implement that tooling.

Migration output is a new derived representation. A writer or migration must
not mutate the original capture evidence in order to make it readable.

These are policy rules only in PL-0006. No reader, writer, schema validator,
or release implementation is created here.

## 6. Migration policy

Migrations are explicit, versioned operations. Every migration path must name
both its exact **source schema version** and its exact **target schema
version**, and must declare the capabilities and assumptions used along the
path.

Migration rules:

- Migration is non-destructive relative to the original `.packscan` evidence.
  The source package, photos, metadata, and provenance remain available for
  audit and reprocessing.
- A migration produces a new derived representation. It must not perform an
  in-place rewrite of the immutable source package.
- A migration failure is reported with source version, target version, stage,
  and diagnostic details where available. It must not partially overwrite the
  source or replace a previously valid derived result.
- Downgrade is not assumed to be possible. A downgrade requires an explicit,
  supported path and may be rejected if the target contract cannot represent
  the source faithfully.
- Lossy migration must be explicitly identified, explained, and made visible
  to the user and to the audit record before its derived output is relied on.
- Migration implementations, validators, and user workflows belong to later
  PackScan and application tasks.

## 7. Application-to-schema compatibility declarations

Each future Studio or Capture release must declare, in its release metadata or
other later-approved release artifact:

- its application version (StudioVersion or CaptureVersion);
- the PackScan schema versions or read range it can read;
- the schema version or versions it can write;
- its migration support range and supported migration paths; and
- known incompatibilities, rejected features, and relevant limitations.

These declarations are required even for development-stage `0.y.z` releases.
They are policy requirements, not an implementation of release metadata in
this task. PL-0363 and PL-0364 remain responsible for coordinated release
numbering and release-manifest implementation. PL-0006 creates no release
manifest.

## 8. Release bump examples

The following examples show how to apply the rules. They are examples of
classification, not frozen release decisions:

| Change | Version result |
| --- | --- |
| Studio bug fix with no intended public compatibility change | Studio PATCH, for example `0.1.0` -> `0.1.1`. |
| New backward-compatible Studio tool | Studio MINOR, for example `0.1.0` -> `0.2.0`. |
| Incompatible Studio project-format or runtime contract | Studio MAJOR, for example `0.1.0` -> `1.0.0` (or the next applicable major). |
| Capture UI-only fix that does not change persisted/API behavior | Capture PATCH, for example `0.1.0` -> `0.1.1`. |
| Backward-compatible new Capture capability | Capture MINOR, for example `0.1.0` -> `0.2.0`, with schema impact separately assessed. |
| Incompatible Capture persisted-session or API behavior | Capture MAJOR, for example `0.1.0` -> `1.0.0`. |
| Optional PackScan metadata field that older readers can safely ignore | Schema MINOR, for example `1.0.0` -> `1.1.0`. |
| Required PackScan field removal or incompatible rename | Schema MAJOR, for example `1.0.0` -> `2.0.0`. |
| Documentation-only clarification of existing serialized meaning | Schema PATCH if the clarification records an already-existing contract; no schema bump if it is wording-only and adds no contract clarification. |
| Unit or coordinate-system semantic change | Schema MAJOR, for example `1.0.0` -> `2.0.0`, with explicit migration/support analysis. |
| Checksum interpretation change that breaks older readers | Schema MAJOR, for example `1.0.0` -> `2.0.0`. |

An optional metadata field is not automatically a MINOR change: older readers
must be able to ignore or safely handle it under the contract. Likewise, a
required-field rename, unit change, coordinate-frame change, or breaking
checksum interpretation cannot be hidden in a PATCH.

## 9. Git, releases, and provenance

Git tags and GitHub releases are later release activities. This policy creates
none. One PackLab monorepo may contain different StudioVersion,
CaptureVersion, and PackScanSchemaVersion values at the same time. Task IDs
such as `PL-0006` are work identifiers, not semantic versions. A Git commit
SHA is provenance, not a semantic version.

When later release artifacts are implemented, they must record the exact
semantic versions of the relevant applications and schema, together with the
commit provenance used to build or publish them. Release artifacts must not
replace semantic versions with a SHA, and a SHA must not be treated as a
compatibility declaration.

## 10. Architecture and safety boundaries

Versioning does not change PackLab's architecture boundaries:

- Original `.packscan` input and capture evidence remain immutable.
- Millimetres remain canonical engineering units unless changed by a future
  audited ADR.
- Coordinate systems, photo orientation, calibration meaning, checksums, and
  required file semantics remain explicit contracts.
- Scan Mesh, Scan Master, and Design Model remain separate concepts. A
  version number does not turn a reference Scan Mesh or Scan Master into an
  editable Design Model, and a rendered/UI representation is not dimensional
  source of truth.
- Public-repository safety remains in force: secrets, credentials, signing
  material, private scans, confidential supplier files, and proprietary
  production artwork do not belong in this policy or the repository.
- No release implementation, schema implementation, or application-version
  implementation is pulled forward into PL-0006.

This document is not a second project-status tracker. Task lifecycle and
current-state truth remain solely in root `TASKS.md`.

## 11. Version source-of-truth hierarchy

Future implementation and release work must use this precedence:

1. The serialized PackScan package declares its own PackScanSchemaVersion.
2. Built PackLab Studio binaries expose their own StudioVersion.
3. Built PackLab Capture binaries expose their own CaptureVersion.
4. A later release manifest records compatibility and build provenance.
5. The Git commit SHA supplements provenance but does not replace semantic
   versions.

H!veAI and root `TASKS.md` describe project workflow and lifecycle state. They
are not sources of StudioVersion, CaptureVersion, or
PackScanSchemaVersion truth.
