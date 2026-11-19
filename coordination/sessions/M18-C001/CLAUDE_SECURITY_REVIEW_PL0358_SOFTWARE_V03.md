# PL-0358 - security review V03 of the profile-path and failure-category diff

Reviewer: Claude security/license reviewer (non-implementing, read-only). HEAD 85028a65 plus the uncommitted diff to .github/workflows/packlab-capture-signed-ipa.yml and tests/ci/test_capture_signed_ipa_workflow.py.
Context: hosted run 44575023673 failed at archive, and only the count line was printed. No edits, no git writes, no dispatch, no secret read. I did not open the run log.

## Checks run
- pytest test_capture_signed_ipa_workflow + test_ios_artifact_provenance + test_ci_data_safety: 64 passed, 1 skipped. ci_data_safety guard: PASS. ruff: clean.
- Behaviour test of the extracted report_failure under real bash, using an adversarial log: a cert CN "Apple Distribution: NAME (TEAMID)", a quoted profile name, team ID, NUL/binary bytes and a literal "$(id)".
  - Output was only "failed with 4 error line(s)" and "profile=1 certificate=2 entitlement=1 team=1 compile=1".
  - No log text, CN, team or profile name was printed, and $(id) was not evaluated.
- Mutants on temp copies: 5 of 8 killed.
  - Killed: grep without -c, grep -o, echo of $(<"$log"), an extra line-reader helper, a catch-all category pattern.
  - Survived: removal of the UserData path from install, from the early delete, and from the always() cleanup (see P3-1).

## Leak analysis
- Every category value comes from _n, which is grep -ciE with a fixed literal pattern written in the workflow. -c emits only an integer count per file, so no category pattern can emit matched text.
  - The patterns are workflow constants, not log-derived, so there is no pattern injection.
  - The echo interpolates only counts and $1 (the literal archive/export).
- What a count discloses is the number of matching lines, e.g. team=1. It reveals no identifier. Acceptable for a public log.
- grep stderr on a missing log shows only the runner temp path. The log always exists because the redirect creates it.
- The new install loop uses profile_uuid only in the destination path. profile_uuid is regex-validated, add-masked first, and not echoed.

## Cleanup completeness
- Install writes the profile to MobileDevice/Provisioning Profiles and to Developer/Xcode/UserData/Provisioning Profiles.
- Both paths are removed by the early "Delete temporary keychain once signing is verified" step and by the always() cleanup.
- The always() step also removes the signing dir, the verify dir, the xcarchive, the export dir and DerivedData. This is complete for every file the workflow itself writes.
- Residual (P3-2): Xcode export can leave IDEDistribution logs (.xcdistributionlogs, which contain profile/team info) under $TMPDIR (/var/folders). This is harmless on ephemeral hosted runners.

## Findings
- P3-1 Test gap: no test pins the UserData path in install, the early delete or the always() cleanup (3 surviving mutants). Add an assertion that both profile directories occur in the install loop and in both rm commands.
- P3-2 Self-hosted only: if ever moved off hosted runners, also remove the IDEDistribution logs under $TMPDIR (or run xcodebuild export with TMPDIR set to a dir under RUNNER_TEMP that cleanup deletes).
- P3-3 Cosmetic: if the log is missing, _n prints an empty count and repeated grep errors. Use "2>/dev/null" and a ":-0" default. Not a leak.
- Carried from V02, still open before ticking PL-0358: P3-A, the exact-line assertion for the codesign verify line (deletion or "|| true" still survives).
- Process: for the evidence record, the coordinator should confirm that the public log of run 44575023673 shows only the count line and masked values.

## Verdict
SOFTWARE_PASS_WITH_NOTES. The diff is safe: no category pattern or echo can print log text, the team ID, a certificate common name or a profile name, and cleanup covers both profile directories on both paths. PL-0358 stays EXTERNAL_PENDING until a successful signed run passes a separate log review. Fix V02 P3-A before ticking.
