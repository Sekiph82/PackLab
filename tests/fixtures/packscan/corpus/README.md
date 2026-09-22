# PackScan validation fixture corpus

This directory is a tiny, synthetic, public corpus for the PackScan 1.0
manifest/version boundary. It contains JSON text only; it contains no camera
bytes, private scans, owner identifiers, supplier material, credentials, or
physical measurement evidence.

## Expected outcomes

| Fixture | Expected outcome | Reason |
| --- | --- | --- |
| `valid-manifest.json` | accept as schema `1.0.0` | Complete synthetic manifest with source payload declarations, UTC time, and canonical checksum metadata. |
| `old-version-manifest.json` | reject as `unsupported_version` | Major version `0` requires an explicit versioned migration before current validation; it is not guessed or silently upgraded. |
| `future-version-manifest.json` | reject as `unsupported_future_version` | Major version `2` is newer than the frozen `1.0.0` contract and must be rejected rather than guessed. |
| `corrupt-json.json` | reject as `corrupt_manifest`/JSON parse failure | The file is intentionally truncated and is not valid UTF-8 JSON syntax. |
| `incomplete-manifest.json` | reject as `invalid_manifest` | It is valid JSON but omits required PackScan manifest fields, so it cannot become a package contract. |

The old and future fixtures are intentionally small version-gate sentinels:
the validator classifies the version before interpreting the remaining
manifest shape. They therefore test compatibility policy without embedding
duplicate payload metadata.

## Reproducibility and provenance

The corpus was created by hand-authored deterministic JSON using the frozen
public synthetic values already used by the PackScan contract fixtures:
capture ID `synthetic-corpus-0001`, iOS model label `iPhone 16 Standard`,
UTC timestamp `2026-09-22T09:00:00Z`, source paths under `images/` and
`metadata/`, and lowercase SHA-256 placeholder values. No file was generated
from a device or private input. Reproduce the semantic corpus by copying
`valid-manifest.json` and changing only `schema_version` to `0.9.0` or
`2.0.0`, truncating the JSON for the corrupt case, and removing required fields
for the incomplete case. The exact resulting files are committed here for
review and regression use.
