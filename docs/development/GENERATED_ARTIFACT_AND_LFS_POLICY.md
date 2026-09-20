# Generated-artifact and Git LFS policy

This policy separates maintained source and safe fixtures from local, regenerable, and protected data. It does not migrate existing files, add Git LFS configuration, or make a large sample binary safe merely by storing it in LFS.

## File classes and locations

| Class | Examples | Default location and rule |
| --- | --- | --- |
| Tracked source | Python, Swift, schemas, policies, tests, project files | Normal owned source directories; review and track deliberately |
| Public fixture | Synthetic or redistribution-cleared contract/test data | `assets/` or `tests/fixtures/`; record provenance and permission |
| Generated/intermediate | COLMAP/OpenMVS databases, meshes, masks, previews, exports | User-local `PackLab` work/output roots; regenerate from protected inputs |
| Cache/tool state | Package downloads, model/tool caches, `.venv`, Xcode/SwiftPM products | User-local cache or build roots; never repository source |
| Durable user/project data | Local scans, projects, source evidence, private artwork | Explicit user/project data roots; protected from public Git |

Generated output remains local unless a frozen task explicitly defines a small, reproducible, public-safe fixture or evidence artifact. A generated file is not automatically reviewable, redistributable, or safe.

## Git LFS eligibility

A binary or sample may be considered for LFS only when every condition is true:

- it is public, redistributable, and cleared for repository publication;
- it is necessary to reproduce a documented test, contract, or user-facing example;
- it is stable and versioned rather than disposable build output;
- its contents and provenance can be reviewed, including licensing and privacy;
- it is large or poorly diffable enough that normal Git is materially worse; and
- the owner accepts LFS storage, quota, clone, retention, and availability costs.

The file still needs a bounded task, an explicit path, a provenance note, and an audit-friendly reason for retaining it. LFS pointers do not replace source review or license/privacy review.

## LFS forbidden cases

Do not put private scans, confidential supplier assets, secrets, signing material, unreleased artwork, ephemeral reconstruction outputs, caches, environments, downloaded tool bundles, or easily regenerated intermediates in LFS. LFS must never be used to bypass the public-data boundary, hide a large diff, or preserve an owner file that is not cleared for publication.

## Size, diffability, provenance, and retention

Before retaining a binary, record its approximate size, why a text or synthetic fixture is insufficient, source/license/redistribution provenance, reproducibility inputs, expected change frequency, and whether a fresh clone or CI runner can obtain it. Review LFS quota and pointer availability as part of release planning; an unavailable LFS object must not make a source checkout falsely appear complete. Prefer small deterministic fixtures and metadata over captured production evidence.

No existing file is migrated to LFS by this policy, and no large sample binary is added merely to exercise it. Concrete `.gitattributes`, LFS storage, and release-retention choices require a later scoped change and independent audit.
