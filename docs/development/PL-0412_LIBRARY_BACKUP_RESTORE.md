# PL-0412: Library backup and verified restore on a clean target

**Software half only, tested on synthetic libraries.** No Kenya library, storage medium or clean machine exists yet. Nothing here claims a real backup, a real restore or factory validation. The owner steps below stay pending.

## Tool

`tools/dev/library_backup.py` (stdlib only; it reuses the PL-0418 `scan_copy_manifest` file-list format and its link and unreadable-entry rules):

```
python -m tools.dev.library_backup backup  LIBRARY_ROOT NEW_BACKUP_SET
python -m tools.dev.library_backup restore BACKUP_SET EMPTY_TARGET --expect-manifest-sha256 HEX [--writable]
python -m tools.dev.library_backup verify  BACKUP_SET RESTORED_ROOT --expect-manifest-sha256 HEX
```

Exit codes: 0 = PASS, 1 = FAIL (a JSON report is printed), 2 = refused precondition.

### Backup set

A backup set is `NEW_BACKUP_SET/manifest.json` plus `NEW_BACKUP_SET/data/...`. The manifest (`packlab.library-backup-set.v1`) contains:

- the tool version;
- the PL-0418 file list (relative POSIX path, size and SHA-256 for each file);
- a `manifest_sha256` over everything else in the manifest.

When the root is a Studio Packaging Library (it has `packaging-library-state.json`), the manifest also pins:

- the state revision and the audit head;
- the revision of each asset;
- each SKU's revision and its asset binding;
- every attachment id.

To get these values, the tool opens the staged copy with the real `PackagingLibraryAuditStore` (which replays the full audit chain) and `PackagingLibraryStore` (which reads and verifies every attachment record). The manifest holds no absolute paths and no timestamps, so the same library always produces the same bytes.

Safety rules:

- **Links are refused.** Symlinks and NTFS junctions inside the root, the root itself, or any ancestor of the root or the destination are refused. Unreadable entries are refused.
- **Work is bounded.** The defaults are 100,000 files and 64 GiB. An `lstat` pre-walk checks them before anything is hashed. Callers may lower the bounds but not raise them above the restore defaults, because a larger set could never be restored.
- **Names must be portable.** Backup refuses any file name that restore would reject (see Restore step 1), so it never publishes a set that can't be restored.
- **Overlap is refused.** The destination may not be inside the library root, and the root may not be inside the destination.
- **Existing sets are never overwritten.** A backup set that already exists is never replaced. After publishing, the files in a new set are made read-only.
- **Writes are atomic.** The tool copies into a hidden sibling folder (`.<name>.partial-*`). It re-hashes every file during the copy, and a file that changed since it was hashed aborts the backup. Every file and the manifest are fsynced. The manifest is written last, then checked with the same rules restore applies, and the folder is renamed into place only after that. A folder without a manifest never verifies.

### Restore

The target must be a missing or empty folder that is not a link. It must not overlap the backup set in either direction, and its parent must be a folder that can be created and that is not reached through a link. Restore runs in this order:

1. Validate the manifest:
   - contract;
   - self-digest;
   - the digest you supply, which should come from the work record;
   - tool version;
   - file list;
   - path safety: these are rejected:
     - absolute paths, drive letters, `:`, `\`, `..`, `.` and empty segments;
     - non-printable characters;
     - segments ending in a dot or a space;
     - Windows device names (CON, PRN, AUX, NUL, CONIN$, CONOUT$, COM1-9, LPT1-9, also with an extension);
     - paths that differ only by letter case;
   - non-finite JSON numbers (NaN, Infinity), and nesting too deep to parse (these give `manifest_unreadable` instead of a crash);
   - bounds.
2. Compare the backup set's `data/` folder with the manifest **before anything is copied**.
3. Copy into a hidden staging folder next to the target, re-hashing each file.
4. Run the full verification on the staging folder, including the semantic re-open.
5. Rename the staging folder to the target. If anything fails, nothing is published, and the target stays missing or empty.
6. Make the restored files read-only. Studio opens the library lock file for writing, so a read-only restore cannot be edited in Studio until the read-only attribute is cleared. Use `--writable` (or `read_only=False`) when the restore will be opened and edited in Studio. Keep the default for archive copies and drills.
7. Verify the target again and return that report.

### Verification report

The report (`packlab.library-restore-verification.v1`) gives:

- a `verdict` of PASS or FAIL;
- sorted `reasons`;
- the `manifest_sha256` it was checked against;
- the library state revision;
- `semantic_check`: `library_reopened`, `no_library_state`, `failed` or `skipped`;
- a `report_sha256` over the rest of the report.

Corruption classes are reported as:

- `missing`
- `unexpected`
- `renamed: a -> b` (same size and digest, but a different path)
- `truncated`
- `grown`
- `altered` (same size, different digest)

Restoring the same backup twice produces identical reports.

The semantic check re-opens the restored root through the same loaders used for backup. It requires the state revision, audit head, asset revisions, SKU bindings and attachment ids to equal the values pinned in the manifest. So a tampered state file whose manifest entry was also rewritten still fails (`semantic_load_failed`), and a manifest whose revisions were forged and re-signed fails with `semantic_mismatch`.

## Limits

- **The self-digest only catches accidental damage.** Anyone who can write the backup set can re-sign the manifest. Tampering is caught only when the `manifest_sha256` recorded off-band in the work record is passed with `--expect-manifest-sha256`.
- **Empty folders are not recorded**, the same as in PL-0418.
- **The destination check is not fully atomic on POSIX.** The destination is checked before the final rename. On POSIX, if an empty folder is created at the destination in that short window, the rename can still succeed. Windows `rename` refuses an existing target.
- **The overlap checks compare spelled paths.** `WindowsPath` comparison is case-insensitive, so case variants are caught. Paths are not resolved, though, so an 8.3 short name or a junction/`subst` alias of the same folder can get past the overlap checks. Links in ancestors are still refused.
- **Copy failures can include absolute paths.** Reasons for an unreadable entry or a failed copy may contain local absolute paths. Do not publish raw reports from real runs.
- **Staging race.** Staging folders are created in the destination's parent folder. A local user who can write there could swap a staging subfolder for a junction between creating it and writing a file into it. That would cause a create-only write of manifest-bound bytes outside the target. The post-copy verification still refuses the link, and Python 3.12 `rmtree` does not follow junctions. Hostile local users are out of scope: use a destination parent that only the operator can write.
- **Folder durability.** Folder entries are not fsynced, because Windows does not support it. After a power loss, a set may be missing, and a set that exists either verifies or fails verification.
- **Read-only is a guard, not protection.** It sets the file mode bits only (the Windows read-only attribute), not ACLs. It is not tamper protection.
- **Packaging Library loaders only.** Semantic checks cover the Packaging Library state, records and attachments. Raw-capture folders are verified byte for byte only, because there is no semantic loader for them in this tool.
- **Separate from the Studio ZIP backup.** The Studio ZIP backup (`PackagingLibraryBackupService`, 512 MiB cap) is unchanged. This tool is the folder-level set for larger libraries plus raw captures.

## Synthetic tests

`tests/ci/test_library_backup.py` builds every library under `tmp_path` with `SYNTHETIC` ids. Each library has one asset, one SKU bound to that asset, one attachment record and blob, and one raw capture. The tests cover:

- **Round trip:** backup, restore and re-open, with SKU-to-asset bindings and the state revision checked, the files left read-only, and CLI `verify`.
- **Determinism:** the same manifest bytes and identical reports, with no tmp path in the manifest.
- **Corruption classes:** missing, extra, truncated, bit-flip and rename in the backup set. Each fails and publishes nothing. Corruption after a restore is detected.
- **Path traversal:** a re-signed manifest with a `..`, absolute, drive, backslash or empty-segment path is rejected.
- **Manifest tampering:** a self-digest mismatch, forged and re-signed revisions (`semantic_mismatch`), and the off-band digest check (`manifest_digest_not_expected`).
- **State tampering:** a state file tampered and re-signed is caught by the real audit loader.
- **Half-written backup:** a set with no manifest fails.
- **Crashes:** a simulated crash during backup or restore leaves no set, no target and no staging folder.
- **Refused preconditions:** a non-empty target (the owner's file is untouched), the file and byte bounds, and destination overlap.
- **Links:** a junction or symlink inside the root and in an ancestor is refused. The test is skipped only if neither can be created. An unreadable entry is refused.
- **Plain folder:** a folder without library state is verified byte for byte only.
- **Security review V01 fixes:**
  - **Overlap:** a restore target inside or equal to the backup set is refused, and the set is left untouched.
  - **Source changed after hashing:** a source file that changes between the manifest and the copy aborts the backup ("file changed during copy"), and no set is published.
  - **Attachment blob:** a byte flip in an attachment blob, with the manifest re-signed, fails with "attachment does not verify".
  - **Hostile JSON:** a deeply nested state file, a deeply nested manifest, and NaN or Infinity in the manifest each give FAIL instead of a crash.
  - **Re-signed manifest guards:** `:`, a control character, reserved device names, trailing dot or space, a case collision, an unsupported tool version and a non-dict library section are each rejected.
  - **Bounds:** caller bounds above the defaults are refused, and the restore pre-walk and manifest bounds are enforced.
  - **Unrestorable names:** backup refuses a library containing `aux.txt`.
  - **Read-only:** the backup set is read-only, and `--writable` leaves a restore writable.
  - **Final re-verify:** damage after publishing is caught by the final check.
  - **Links and parents:** a link at the restore target, a parent that is a file, and a linked destination ancestor are refused for both restore and backup.

## PHYSICAL/OWNER steps (pending)

These require the accepted real library and owner hardware. They stay open and are not claimed:

1. Run `backup` on the accepted Kenya library onto a **physically separate** disk. Record the printed `manifest_sha256`, the date, the operator and the medium in the work record.
2. On a **clean machine or clean user profile** (not the capture machine and not a mapped path from it), run `restore` with `--expect-manifest-sha256`. Only `"verdict": "PASS"` with `"semantic_check": "library_reopened"` counts.
3. Open the restored library in Studio and spot-check SKUs, assets and attachments. Restore with `--writable` (or clear the read-only attribute on a scratch copy) for this step, because Studio needs write access to the lock file.
4. Apply the PL-0418 retention and 3-2-1 policy: encrypt off-site media and log every restore. Retention and deletion periods wait for owner and legal decisions.
5. Never commit real backup sets, manifests or reports to this public repository.
