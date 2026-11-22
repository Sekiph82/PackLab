# Security review: PR #35 owner-dev keep-one-previous (V01)

Source: fa0e951c (branch chore/owner-dev-keep-one-previous). Reviewer did not author it.

- Deletion only runs after successful promotion. Failure paths rethrow before it. Matches are limited to direct children of OwnerRoot named `^previous-[0-9a-f]{32}$` (a name only this script creates), and removal uses `-LiteralPath`.
- PS 5.1.26100 test in scratchpad: Remove-Item -Recurse removed a nested junction and a top-level junction `previous-*` without touching their targets.
- If `$previous` is null (current was absent or a junction), every old copy is deleted. Acceptable because immutable `releases/<id>` stays as rollback.
- pytest: 7 passed.
- Nits (non-blocking): `-match` is case-insensitive; the third-switch assert does not check which runtime was kept; no junction regression test; directory symlinks (mklink /D) were not tested.

Verdict: PASS (deletion safety). Release gates remain unchanged.
