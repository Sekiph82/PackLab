# PL-0412 software half: independent security and code review V02 (re-review of V01 fixes)

- Reviewer: independent Claude security/licensing reviewer. I am not the implementer. I made no source edits and no git writes, and I did not touch the PL-0411 files.
- Base: main @ 8e8c11470c04007dc9addb3b5eb85a1ffcb6449e. Re-read the untracked tools/dev/library_backup.py (427 lines), tests/ci/test_library_backup.py and docs/development/PL-0412_LIBRARY_BACKUP_RESTORE.md.
- All probes and mutants ran on temp copies under TEMP.

## Checks run

| Check | Result |
|---|---|
| pytest tests/ci/test_library_backup.py tests/ci/test_scan_copy_manifest.py | 59 passed |
| ruff 0.16.8 (locked .venv): ruff check core apps tools tests | All checks passed |
| ruff format --check with line-ending=auto (both files) | already formatted |
| mypy tools/dev/library_backup.py | no issues |
| Secret and PII grep of all 3 files | clean |
| Dependencies | stdlib only, unchanged |

## V01 findings, re-verified

| ID | Fix (code location) | Evidence | Status |
|---|---|---|---|
| P2-1 | Two-way overlap refusal in restore (:355-356) | Probes: SET/data/inside, SET/x and a case-variant SET/data/y are all refused. The set restores cleanly afterwards. Mutant drop_restore_overlap is KILLED. | CLOSED |
| P2-2 | Imports fixed | The CI ruff command is clean under the locked 0.16.8. | CLOSED |
| P2-3 | New tests: changed-during-copy (test 377) and re-signed attachment flip (test 409) | Mutants drop_copy_rehash and drop_attachment_verify are both KILLED. | CLOSED |
| P3-1 | Parametrised guard tests (437-458, 473-540) | printable, trailing, reserved, case, bounds, tool_version, library type, parent links, target link, read-only and final re-verify mutants are all KILLED. | CLOSED |
| P3-2 | parse_constant reject, RecursionError catch (:252-254, :215, :332), parent mkdir wrapped (:114-119) | Probes: deep nesting, NaN and Infinity give manifest_unreadable on both restore and verify. A file as the parent gives a refusal (exit 2), not a traceback. A deeply nested state file gives semantic_load_failed. | CLOSED |
| P3-3 | Reserved stems and trailing dot or space rejected (:81-100) | Probes: NUL.txt, com1, lpt9.dat, CONIN$ and nul. are refused at backup and nothing is published. Trailing-dot and trailing-space names in the source are refused via lstat. | CLOSED (note N2) |
| P3-4 | Bounds cap (:189-190), unsafe names refused before staging (:201-203), self-check of the manifest before rename (:231-233) | Probes: max_files=10**6 is refused; reserved names are refused. | CLOSED (note N1) |
| P3-5 | Doc line 97 now accurate (case-insensitive; 8.3, junction and subst aliases not resolved) | Text read | CLOSED |
| P3-6 | --writable flag (:397-400, :414); doc step 6 and owner step 3 | Mutant drop_writable_flag is KILLED. | CLOSED |
| P3-7 | Manifest fsync (:226-229) | Code read. Not testable, so its mutant survives (expected). | CLOSED |
| P3-8 | Staging race documented (doc line 99, code comment :235-236), not mitigated | Acceptable while hostile local users are out of scope. | ACCEPTED AS DOCUMENTED |
| P3-9 | Absolute paths in reasons; still disclosed (doc line 98) | Observed again in the stderr refusal for a trailing-dot name. | ACCEPTED AS DOCUMENTED |

## Mutation testing (32 mutants, fresh temp copy each)

- 27 killed, 5 survived.
- Survivors and why each is acceptable:
  - drop_dotdot: a dot-dot segment is still rejected by the trailing-dot rule (it ends in a dot). The guard is redundant, not missing.
  - drop_colon: the test value a:b is also caught by the drive check (PureWindowsPath gives drive a:). A nested x/a:b would only be caught by the colon rule. See N3.
  - drop_selfcheck: unsafe names and bounds are already refused before staging, so the manifest self-check is unreachable defence in depth. See N1.
  - drop_sku_missing_asset: the audit loader already rejects an SKU that binds a missing asset. This check is redundant.
  - drop_manifest_fsync: durability cannot be observed in a unit test.

## Notes (non-blocking)

- **N1.** The self-check at :231-233 has no test that reaches it (its mutant survives). It is harmless defence in depth. Optionally, add a monkeypatched test that corrupts the staged manifest.
- **N2.** The reserved set omits COM0 and LPT0, which current Microsoft naming guidance also lists. The risk is negligible on supported Windows. Add them for completeness.
- **N3.** Add a nested colon case (for example d/a:b) to the parametrised guards, so the colon rule is discriminated separately from the drive rule.
- **N4.** Doc line 100 says "a set that exists is never half-valid". That is slightly stronger than proven. Suggested wording: "a set that exists either verifies or fails verification; it never silently passes". Every file and the manifest are fsynced before the rename, and directory entries are not.

## Honesty and gates

- Re-signed manifests without --expect-manifest-sha256 are still disclosed as undetectable for consistent forgeries (doc lines 92-93, docstring 13-14).
- The semantic check still uses the real PackagingLibraryAuditStore and PackagingLibraryStore loaders.
- Physical and owner steps (real Kenya library, separate medium, clean machine, Studio spot-check) remain pending and unclaimed.
- No real sets, manifests or reports are committed.

## Verdict

**SOFTWARE_PASS_WITH_NOTES.** All V01 P2 findings are closed with discriminating tests. The V01 P3 findings are fixed or documented. Notes N1-N4 are optional. Overall status: SOFTWARE COMPLETE / PHYSICAL VALIDATION PENDING. Public or factory release is still blocked until real owner evidence exists.
