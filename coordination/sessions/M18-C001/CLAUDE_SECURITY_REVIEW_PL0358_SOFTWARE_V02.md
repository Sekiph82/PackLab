# PL-0358 software half - independent security/licensing re-review V02

Reviewer: Claude security/license reviewer (non-implementing, read-only). Base HEAD d1ab0618 plus the uncommitted working-tree diff after the V01 fixes.
No edits, no git writes, no dispatch, no settings touched, no secret read. All mutants ran on temp copies only.

## Checks run
- pytest test_capture_signed_ipa_workflow, test_ios_artifact_provenance, test_ci_data_safety, test_offline_release_manifest, test_artifact_upload_guard_conditions: 92 passed, 2 skipped.
  - The bash behaviour test test_failure_report_emits_only_a_count RAN (it was not skipped).
- ci_data_safety.py --scan-text --check-workflows --check-signing-secrets: PACKLAB_CI_DATA_GUARD=PASS.
- ruff check + format --check on the 3 Python files: clean. mypy (configured scope): success, 300 files.
- Workflow mutants (temp copy of the yml, test module pointed at it): 30 of 35 killed.
  - All 21 V01 mutants are killed except codesign removal.
  - Also killed: printenv, env pipe, cat plist, team_id to summary and to stdout, cat log on failure, grep -i lines in report_failure, tail inside report_failure, add-mask removal, expiry removal, method allow-list removal, p12 rm removal, unfiltered find-identity, export cleanup removal, early keychain step removal.
- Provenance mutants (temp copy of the tool + test): 6 of 6 killed.
  - Mutants: origin check, workflow-name check, .ipa check, verify-side file count, sdk rule, SIGNED state.
  - The unmutated baseline passes in the same temp layout.

## V01 findings - status
- P2-1 FIXED.
  - packlab-capture-signed-ipa.yml:307-332: xcodebuild archive/export output goes only to runner log files.
  - report_failure prints only "failed with N error line(s)".
  - The bash test feeds a log with cert CN, team and profile name and asserts none are printed. Mutating report_failure to print lines or a tail is killed.
- P3-1 FIXED: RUN_DENYLIST, the team_id/profile_uuid usage rule, the summary rule, add-mask/expiry/allow-list/p12-rm asserts (test file lines 182-233). Remaining evasions are listed under P3-A.
- P3-2 FIXED: cleanup line 436 adds packlab-signed-export and packlab-capture-archive-derived-data.
- P3-3 FIXED.
  - Lines 370-377 delete the keychain, the installed profile, profile.mobileprovision and profile.plist right after verify, before both uploads.
  - add-mask from the install step persists for later steps, so profile_uuid in that step is masked.
  - The always() cleanup stays as backstop.
- P3-4 FIXED: lines 197-198 restrict the method to the allow-list.
- P3-5 FIXED.
  - For ios_signed_ipa, tools/ci/ios_artifact_provenance.py requires .ipa, event_name workflow_dispatch and the exact workflow name. It also requires a single file in both build_manifest and verify_manifest.
  - The workflow env matches (GITHUB_WORKFLOW = "PackLab Capture Signed IPA", event workflow_dispatch).
  - The doc (lines 39-43) states that SIGNED is not SIGNED_VERIFIED.
  - offline_release_manifest.py is unchanged and still requires SIGNED_VERIFIED plus signature evidence.
- P3-6 DOCUMENTED (doc lines 72, 96-100): repo-level secrets prohibited, self-hosted caveat, the deployment-branch policy is the real boundary.

## Remaining findings (none blocking the software half)

### P3-A Two codesign-verify survivors, deletion and "|| true"
tests/ci/test_capture_signed_ipa_workflow.py:162 only checks that the substring "codesign --verify --deep --strict" occurs in the verify step. The summary echo at workflow line 368 also contains it. So both mutations survive:
- deleting the actual line 348;
- appending "|| true" to it.

This is the only check that justifies SIGNED in the sidecar. It is not a secret leak, and a credentialed run still needs a separate log/evidence review, so I do not block the software half on it.

Judgment: REQUIRED before PL-0358 is ticked; cheap. Assert that a stripped line in the verify run equals exactly:
/usr/bin/codesign --verify --deep --strict "$app_path" > /dev/null 2>&1
Also assert that "set -euo pipefail" is the first line, and that the line sits before the summary echo.

### P3-B Denylist evasions survive (inherent limits of a static denylist)
These survive:
- python3 printing signing.json;
- plutil -p of profile.plist;
- security cms -D ... -o /dev/stdout;
- in the mutant where it was added to the install step, security find-certificate -a -p (it was killed, but only through the NextLevel identity test, not the denylist).

Optional: add plutil -p, "-o /dev/stdout" or "-o -", security find-certificate and dump-keychain to RUN_DENYLIST. Human review of any workflow diff remains the primary control.

### P3-C Cosmetic
packlab-capture-signed-ipa.yml:436 has a long run of spaces between "...PackLabCapture-signed.xcarchive" and the next path, apparently a lost backslash-newline continuation. It works functionally because the spaces just separate arguments. Tidy it.

### P3-D Nit
_check_signed_ipa_file_count accepts a directory that holds exactly one file. Optional: also require that the artifact root is a regular file for ios_signed_ipa.

## Verdict
SOFTWARE_PASS_WITH_NOTES.

PL-0358 remains EXTERNAL_PENDING: Apple credentials, a protected ios-signing environment (main-only deployment branch, required reviewer, environment-scoped secrets), a hosted signed run on an exact main SHA, and a separate log review. P3-A should be fixed before the task is ticked. The task must stay unchecked until real signed-run evidence exists.
