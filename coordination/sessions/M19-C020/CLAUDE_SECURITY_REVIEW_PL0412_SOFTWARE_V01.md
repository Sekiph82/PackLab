# PL-0412 software half: independent security and code review V01

- Reviewer: independent Claude security/licensing reviewer. I did not implement this work and I made no source edits or git writes.
- Base: main @ 8e8c11470c04007dc9addb3b5eb85a1ffcb6449e. The files under review are untracked: tools/dev/library_backup.py, tests/ci/test_library_backup.py, docs/development/PL-0412_LIBRARY_BACKUP_RESTORE.md.
- Scope: software only. Physical and owner acceptance (real library, separate medium, clean machine) stays PENDING.

## Checks run

| Check | Result |
|---|---|
| pytest tests/ci/test_library_backup.py tests/ci/test_scan_copy_manifest.py | 35 passed |
| ruff check core apps tools tests (the CI command, .github/workflows/windows-python-quality.yml:105) | **1 error: I001** at tests/ci/test_library_backup.py:7 |
| ruff format --check with line-ending=auto | clean |
| mypy tools/dev/library_backup.py | clean |
| Secret and PII grep of all 3 files | clean (synthetic ids only, no absolute paths, no tokens) |
| New dependencies or licences | none (stdlib only) |

## Probes

All probes ran in TEMP directories only.

- **Restore into the backup set** (restore SET SET/data/inside): verdict PASS. Afterwards every restore of SET fails with "unexpected: inside/...".
- **Restore into the set root** (SET/x): PASS. The set is polluted.
- **Deeply nested manifest** (200000 nested lists): uncaught RecursionError.
- **Manifest containing NaN**: uncaught ValueError from _canonical(allow_nan=False) at line 211.
- **Target parent is a file**: uncaught FileExistsError from line 309.
- **Case-variant overlap** (create_backup(src, SRC/inner)): refused correctly. The doc says otherwise; see P3-5.
- **Windows names injected through the extended-length path prefix plus a re-signed manifest**:
  - CON, CONIN-dollar, PRN, COM1 and aux.txt are ordinary files on this Win11 build. They restore and pass.
  - NUL is read as the device and fails as truncated.
  - Names with a trailing dot or a trailing space are refused (unreadable entry).
  - Nothing was written outside the target.
- **Traversal paths** (dot-dot, absolute, drive letter, backslash, double slash): rejected. There is a second guard as well: every manifest path must equal a real os.walk entry under data/ before copying (lines 313-314). So a crafted manifest cannot name a file outside the set.
- **Mutation testing**: 21 mutants, each in a fresh temp copy. 7 killed, 14 survived:
  - Killed: drop dot-dot check, drop pre-copy compare, drop staging verify, drop semantic re-open, drop off-band check, drop self-digest.
  - Survived: drop colon check, drop isprintable, drop case-collision, drop manifest bounds, drop restore _check_bounds, drop tool_version check, drop library-type check, **drop copy re-hash**, **drop attachment store.verify**, drop SKU-binding check, drop backup-set read-only, drop final re-verify, drop restore-target link refusal, drop restore and backup destination-ancestor link refusal.

## Findings

### P1
None. I found no write outside the target from a crafted manifest or crafted data/ contents.

### P2

**P2-1. Restore can write into the "immutable" backup set and corrupt it.** Evidence: tools/dev/library_backup.py:304-310 and :317.
- restore_backup checks overlap between the target and the backup set in neither direction. restore SET SET/data/x and restore SET SET/x both PASS, but they publish into the set.
- After that, every later restore of the set FAILs (unexpected: ...). The planted files are read-only, which makes cleanup harder.
- One mistyped path therefore breaks the only verified copy of the library.
- Fix: mirror line 162 in restore. Refuse when destination.is_relative_to(source) or source.is_relative_to(destination), and add a test.

**P2-2. Lint error will fail CI.** Evidence: tests/ci/test_library_backup.py:7-29.
- Ruff I001: the packlab_core and packlab_studio imports are grouped wrongly.
- CI runs ruff check core apps tools tests.
- Fix: ruff check --fix tests/ci/test_library_backup.py.

**P2-3. Two headline safety claims are untested; their mutants survive.**
- _copy_verified at :104: the re-hashing-during-copy check (a file changed since it was manifested) can be deleted and every test still passes.
- _library_summary at :139: store.verify(record) can be deleted and every test still passes. No test tampers an attachment blob and re-signs the manifest.
- Fixes:
  - Change a source file between the manifest and the copy, and assert "file changed during copy" with no published set.
  - Flip one byte of the attachments/ blob, re-sign the manifest, and assert "attachment does not verify".

### P3

**P3-1. Untested claimed guards** (survivors listed above): colon, control characters, case collision, manifest and restore bounds, tool_version, link at the restore target, destination-ancestor links, read-only backup set, final re-verify. Most are defence in depth behind the pre-copy compare, but doc line 52 lists them as behaviour. Add one parametrised re-signed-manifest case for each.

**P3-2. Malformed manifests crash instead of returning FAIL.**
- :204: json.loads raises RecursionError, which is outside (OSError, ValueError).
- :211: _sha256(body) raises ValueError on NaN or Infinity, outside the try.
- :309: mkdir raises FileExistsError.
- Nothing is published, but the CLI exits 1 with a traceback.
- Fix: catch RecursionError, use parse_constant to reject NaN and Infinity, and wrap the precondition mkdir in LibraryBackupError.
- The same RecursionError can come from a nested state file through _library_summary (:121, :286).

**P3-3. Windows device and portability names are not rejected** (_safe_relative, :81-89).
- NUL, and on older Windows also CON, COMn, LPTn and AUX in subdirectories, are opened as devices by the pre-copy _files compare. That can block, and on Win10 the copy could write to a device.
- Trailing dot or space names are refused only by accident (via lstat failure).
- Fix: reject reserved stems and segments ending in a dot or a space, at backup time as well as restore time.

**P3-4. Backup does not self-validate its own manifest before publishing** (:172-189).
- A Linux or case-sensitive library with colon, backslash, case-twin or control-character names is published, and is then permanently refused at restore.
- max_files/max_bytes above the defaults also produce a set that restore refuses (:226 uses the defaults).
- Fix: run the _load_manifest checks on staging before the rename, or forbid bounds above the defaults.

**P3-5. Doc inaccuracy** (PL-0412_LIBRARY_BACKUP_RESTORE.md:90).
- The doc says "not case-folded on Windows". In fact WindowsPath.is_relative_to is case-insensitive, and the probe was refused.
- The real gap is 8.3 short names and junction or subst aliases, because the spelled paths are not resolved.

**P3-6. Restored library is read-only by default, and the CLI has no opt-out** (:301, :358-360).
- The Studio audit lock opens .packaging-library-state.lock with O_RDWR (packaging_library_audit.py:763), so a restored library cannot be edited in Studio until the attributes are cleared.
- Fix: document this in owner step 3, or add --writable.

**P3-7. Durability** (:187-189).
- The manifest is not fsynced before the rename. On power loss the result is fail-safe (manifest_unreadable), but the backup is lost silently.

**P3-8. Staging TOCTOU** (:94-97). Low risk.
- A local actor who can write the destination parent can swap a staging subdirectory for a junction between mkdir and the exclusive-create open. That causes a create-only write of manifest-bound bytes outside the target.
- Post-copy verification then refuses the link, and Python 3.12 rmtree does not traverse junctions.
- Fix only if a hostile local user is in scope.

**P3-9. Private-path leakage in reports** (:235, :287, :330, :78). A verify report was observed containing "unreadable: not a directory: C:/Users/(owner)/...". The doc discloses this (line 91). Optionally, relativise the paths.

## Honesty and gates

- Docstring lines 13-14 and doc lines 85-87 state correctly that a consistently re-signed manifest passes without --expect-manifest-sha256. Forged revisions alone fail semantic_mismatch.
- The semantic check really uses PackagingLibraryAuditStore._load (full chain replay) and PackagingLibraryStore.read_record/verify. relative_path is digest-derived (packaging_library_store.py:83), so it cannot steer _ensure_directory outside the root.
- Physical, owner and legal steps (doc 112-121) remain pending and are not claimed. The doc forbids committing real sets or reports to the public repo.

## Verdict

**FAIL (for acceptance as submitted).** There is no P1. P2-1, P2-2 and P2-3 are small fixes; a narrow re-review after they land can move this to SOFTWARE_PASS_WITH_NOTES. Status: SOFTWARE NOT YET ACCEPTED / PHYSICAL VALIDATION PENDING.
