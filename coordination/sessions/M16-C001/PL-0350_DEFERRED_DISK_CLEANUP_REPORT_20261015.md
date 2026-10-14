# PL-0350 Deferred Disk Cleanup Report — 2026-10-15

## Result

The PackLab-only cleanup ran after PL-0350 evidence was published and handed off. Safe eligible items were processed. The C: free-space check did **not** show a net recovery, so this report does not claim increased free space.

| Measurement | Bytes | Decimal GB |
| --- | ---: | ---: |
| C: free before cleanup | 91,608,444,928 | 91.608 |
| C: free after cleanup | 91,448,082,432 | 91.448 |
| Net change in free space | -160,362,496 | -0.160 |

The measured unique PackLab-root file lengths total 43,787,156,239 bytes before and 40,203,052,471 bytes after the removals (logical file-length accounting, not a claim about allocated NTFS blocks). The AppData PackLab and Codex LocalCache views share the same NTFS directory ID and were counted once. Shared global caches are excluded.

## Removed after verification

- Git worktree `m16-r08-v14/PackLab`: 1,338,455,855 logical bytes. It was clean, its HEAD was contained in `origin/main`, no PackLab process used its path, and no reparse points were present. Removed with normal `git worktree remove`.
- Git worktree `m16-r08-v15/PackLab`: 1,368,060,637 logical bytes. It was clean, its HEAD was contained in `origin/main`, no PackLab process used its path, and no reparse points were present. Removed with normal `git worktree remove`.
- Superseded cold unsigned Installer executable for source `452fe8934b0d56011af8c117555dd059d5c63462`: 877,587,276 bytes, SHA-256 `8cc6fb20e4b88093a8647a5c5c511ee49db0a33de3c6d2c937c14b6544eb30f2`. It was removed only after the newer warm-cache Installer and its installed smoke record both verified PASS. Cold smoke metadata remains retained.

Total verified logical file lengths removed: 3,584,103,768 bytes (3.584 decimal GB). C: free-space readings are the authoritative volume-level result and show no net gain over the cleanup interval.

## Preserved storage and owner data

- Desktop PackLab source, original assets/exports, the pre-existing owner changes, `OwnerDev`, the working application and previous good application versions were excluded from deletion. The three owner checkout changes retain their previously recorded SHA-256 values and Git status.
- OCCT/OCP SDK/runtime checkpoints, source delivery and compliance/audit evidence were retained. PackLab-specific Codex artifact roots account for 3,787,419,571 logical bytes; the measured application/OwnerDev AppData tree accounts for 20,963,527,208 bytes. The alternate Codex LocalCache path is the same directory and is not double-counted.
- Warm-cache Installer retained outside the project checkout: 877,598,790 bytes, SHA-256 `3e7c13c18674fbe0a4de843a2ac329055850d07901a7e33fac8a3dc742d92da6`; its installed smoke evidence says PASS.
- R07 worktree with a clean checkout but a HEAD not contained in `origin/main`, R07 build-timeout worktree with two local changes, OwnerDev worktree, and the currently attached PL-0350 worktree were preserved. The first two account for 1,367,487,302 and 1,369,895,463 logical bytes respectively.
- PackLab-specific pytest fixture sessions 192, 193 and 194 total 11,583,095 bytes. Recursive directory removal was rejected by the system safety policy; no alternate deletion method was used. They remain intact.
- The uv archive cache contains PackLab package metadata but is a shared global cache; it was not changed. No `CMakeCache.txt` was found in the inspected project roots. The discovered Studio build output and Python environments are within protected Desktop/OwnerDev/current or modified/unpushed worktree roots, so they were preserved.

## Owner-data verification and governance

The Desktop checkout still reports its same three pre-existing changes (one tracked modification and two untracked files); their SHA-256 values match the recorded pre-cleanup values. No PackLab executable was running during cleanup, and no PackLab application, OwnerDev release, source tree, original asset/export, SDK/OCP checkpoint, evidence bundle, or root `TASKS.md` was modified. No other project or shared cache was touched.

The two removed R08 worktrees and cold Installer account for the deleted logical bytes above. Recursive pytest cleanup was blocked by system policy; other temporary/source/evidence candidates were preserved where they contain audit material, runtime/source checkpoints, protected OwnerDev data, or worktree state that is not both clean and fully pushed. Repository visibility remains private in accordance with the owner decision. PL-0350 remains **AWAITING_AUDIT**; independent audit and formal legal review are still pending.
