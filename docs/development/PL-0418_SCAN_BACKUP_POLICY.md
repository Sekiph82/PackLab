# PL-0418: Backup cadence and off-machine copy policy for irreplaceable scans

**Planning policy draft. It is not approved for production operation.** No Kenya site, storage hardware or real scan library exists yet. The cadence values are planning values that must be confirmed against the site's actual capture volume, storage and staff. PL-0412 (real backup and restore of the accepted library) stays separate and pending.

## What is irreplaceable

Treat these as irreplaceable, because a physical sample may be gone or changed later:

- raw captures (`.packscan` and project raw-capture folders);
- capture logs and station records;
- PL-0400 checklists;
- calibration evidence.

Derived data (reconstructions, Scan Masters, Design Models, renders) can in principle be regenerated, but it is still backed up because regeneration is slow and non-trivial.

The Packaging Library backup (`PackagingLibraryBackupService`, contract `packlab.packaging-library-backup.v1`) covers library records, thumbnails and attachments only. It is capped at 512 MiB per archive and **does not include raw captures**. Raw scan folders therefore need the separate copy procedure below.

## Cadence (planning values)

| When | What | Where |
| --- | --- | --- |
| Same day as capture, before the sample leaves the station | Each new raw-capture folder: SHA-256 manifest plus a copy | A second, physically separate device (not a second partition) |
| Weekly | Library backup archive (`create_backup` → `validate_backup`) plus all raw-capture folders changed since the last copy | An off-machine copy, with at least one copy off-site or offline |
| Monthly | Restore drill: `restore` the newest library archive into an empty folder and verify a random sample of raw-capture copies | An isolated test location; never the live library |
| Before any change process (PL-0415/0416/0417) or software upgrade | Library backup plus a manifest check of the affected scans | Off-machine |

Keep at least **3 copies on 2 different media, with 1 off-site/offline** (3-2-1). Never treat a sync folder that propagates deletions as a backup.

## Verification

1. Create the manifest on the capture machine:
   `python -m tools.dev.scan_copy_manifest create <scan folder> <manifest.json>`
   The tool refuses to overwrite an existing manifest.
2. Copy the folder and the manifest off the machine.
3. On the destination, run:
   `python -m tools.dev.scan_copy_manifest verify <manifest.json> <copy folder>`
   Only `SCAN_COPY_VERIFY_PASS` (exit 0) counts. Missing, unexpected or altered files fail (exit 1). Symlinks and NTFS junctions are refused, including a copy root that links back to the source. Empty or internally inconsistent manifests are invalid.
4. Library archives must pass `validate_backup` after they are copied.
5. Record the date, operator, manifest SHA-256, destination and result in the work record.

A sample may be released or disposed of only after its raw captures pass verification on at least one off-machine copy.

## Security and privacy

Backups of real captures may contain supplier, customer or confidential package data:

- Never place them in this public Git repository, public cloud links or personal accounts.
- Encrypt removable and off-site media.
- Restrict access to the named roles.
- Log every restore.

Retention and deletion of supplier or customer data follow owner and legal instructions, which are still pending.

## Synthetic dry-run

`tests/ci/test_scan_copy_manifest.py` checks these cases on a synthetic scan folder:

- an identical copy passes, and the tool does not overwrite an existing manifest;
- a copy root, or a nested folder, that is a junction or symlink back to the source fails;
- empty, inconsistent or malformed manifests are invalid, and an empty source cannot be manifested;
- a missing file, an extra file and a single flipped bit are each reported, and a malformed manifest or unreadable copy fails.

The library archive round-trip is covered by the existing `tests/studio/test_packaging_library_backup.py`. No physical storage, Kenya library or restore at a real site is claimed.
