# M06 PackLab project layout

Each project is a versioned directory with a `.packlab-layout.json` marker. The `raw` area is accepted M05 source evidence and is immutable by policy; Studio services never provide an edit or overwrite operation for it.

| Area | Owner in M06 | Portable | Regenerable |
| --- | --- | --- | --- |
| `raw/` | M05 ingest/raw authority | referenced source evidence | no |
| `working/` | M06 editable project state | yes | no |
| `derived/` | M06 provenance and later reconstruction outputs | selectively | yes |
| `cache/` | M06/runtime | no | yes |
| `temp/` | M06 transaction scratch | no | yes |
| `export/` | explicit user exports | explicit only | yes |
| `history/` | M06 operation history | yes | no |
| `recovery/` | M06 crash/recovery markers | selectively | yes after acceptance |

Portable metadata stores project-relative references, UUIDs, revisions and schema versions. It must not store secrets or private absolute source paths. M07 owns reconstruction engines and M09 owns calibrated measurement accuracy; M06 only provides boundaries.
