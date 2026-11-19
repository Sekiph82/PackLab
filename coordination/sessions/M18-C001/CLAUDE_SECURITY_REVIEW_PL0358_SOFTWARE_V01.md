# PL-0358 software half - independent security/licensing review V01

Reviewer: Claude security/license reviewer (non-implementing, read-only). Base HEAD d1ab0618, uncommitted working-tree diff.
Scope: .github/workflows/packlab-capture-signed-ipa.yml, tests/ci/test_capture_signed_ipa_workflow.py, docs/development/PL-0358_SIGNING_OPTIONAL_PATH.md, tools/ci/ios_artifact_provenance.py (diff), tests/ci/test_ios_artifact_provenance.py (diff). No edits, no git writes, no dispatch, no settings touched, no secret read.

## Checks run
- pytest test_capture_signed_ipa_workflow, test_ios_artifact_provenance, test_ci_data_safety, test_offline_release_manifest, test_artifact_upload_guard_conditions: 87 passed, 2 skipped.
- ci_data_safety.py --scan-text --check-workflows --check-signing-secrets: PACKLAB_CI_DATA_GUARD=PASS.
- ruff check + format --check on the 3 Python files: clean.
- mypy (configured scope core/src, apps, tools): success, 300 files. Explicit mypy on the new test reports missing yaml stubs; this matches the pre-existing tests/ci/test_artifact_upload_guard_conditions.py and is outside the configured scope.
- Mutation run on temp copies only: 13 of 21 mutations killed. Killed: secret echo, secrets expression in run, inputs expression in run, secret in argv, pull_request trigger, -A, no environment, default upload true, no always(), set -x, unpinned action, upload of signing dir, drop main guard. Survived: printenv, cat profile.plist, team_id to STEP_SUMMARY, full xcode log on failure, drop add-mask, drop expiry check, drop .p12 rm, and codesign-verify removal when the literal string stays.

## Verified properties
- Trigger is workflow_dispatch only; no workflow_call, workflow_run or pull_request events. This is the only workflow in .github/workflows that references secrets.
- The job if requires dispatch and main. environment: ios-signing. Workflow and job are both contents: read. checkout uses persist-credentials: false.
- Secret references are confined to two places: the presence booleans (lines 55-57) and the install step env (lines 175-177). They are never in run and never in with: of an action. Both inputs are choice/boolean, and the export method is passed via env/argv only, so there is no expression injection.
- Values derived from the profile are regex-validated before use in pbxproj, paths or plist: team [A-Z0-9]{10} and UUID [0-9A-Fa-f-]{36}. Heredocs are quoted.
- Keychain: random openssl rand -hex 32 password, -T codesign -T security, no -A, partition list set. The .p12 is removed right after import. umask 077.
- The always() cleanup also runs on failure, cancel and timeout. It removes the keychain, the installed profile, the signing dir, the verify dir and the archive.
- Actions are pinned by SHA, identical to the existing workflows: checkout 9c091bb, upload-artifact 043fb46.
- The NextLevel resolve step is byte-identical to the unsigned job, and the test asserts this.
- Sidecar fields contain no team ID, UUID, identity or UDIDs. The IPA upload is opt-in (default false) with 1-day retention.
- The provenance diff is correct. ios_signed_ipa requires SIGNED. Non-simulator types now require iphoneos, which matches the device-archive env in packlab-capture-macos.yml:243.
- The release path is unaffected. tools/release/offline_release_manifest.py:379-422 uses a different receipt schema that requires SIGNED_VERIFIED plus a signature-evidence document. A provenance sidecar cannot be passed as a release receipt because its field set mismatches, so the SIGNED sidecar is never auto-promoted to release-grade.
- The provenance tool path filter triggers one hosted macOS unsigned run on push (packlab-capture-macos.yml:11,20). That run is acceptable and useful: it is the regression check that unsigned sidecars still validate under the new sdk rule. It has no secrets.

## Findings

### P2-1 Failure-path log redaction is case-sensitive and incomplete; the logs are public
.github/workflows/packlab-capture-signed-ipa.yml:305 defines redact() as a case-sensitive grep -Ev on "Signing Identity|Provisioning Profile|DEVELOPMENT_TEAM|TeamIdentifier|Team ID". Lines 314 and 322 apply it to an 80-line tail.

Typical Xcode errors are not matched:
- Provisioning profile "NAME" does not include signing certificate "Apple Distribution: PERSON NAME (TEAM)" uses a lowercase "profile".
- ... matching team ID "TEAM" uses a lowercase "team".

The team ID is masked by add-mask, but the certificate common name (often the personal name of the owner) and the profile name are not. Actions logs of a PUBLIC repo are world-readable. The first credentialed run is the most likely to fail: the residual-risk section of the doc notes that PROVISIONING_PROFILE_SPECIFIER=UUID may be rejected.

Fix (any one):
- (a) Do not print xcodebuild output at all. Print only the count of "error:" lines plus a fixed message, and keep the logs on the runner.
- (b) Print only case-insensitive "error:" lines, with every double-quoted substring replaced by a placeholder and any parenthesised 10-character team token replaced too.

Add a test asserting that the failure path never emits the raw log.

### P3-1 Test gaps for leak/hardening properties (mutation survivors)
tests/ci/test_capture_signed_ipa_workflow.py does not fail on any of these:
- printenv/env or cat profile.plist added to the install step (this would dump UDIDs and team);
- team_id written to GITHUB_STEP_SUMMARY;
- removal of the add-mask lines;
- removal of the expiry check;
- removal of the .p12 rm -f;
- full-log cat on failure.

Fix: add string assertions for add-mask (both values), the p12 rm, and the expiry/team/app-id raise messages. Add a denylist (printenv, bare env, cat of plist/mobileprovision/.log, set -x) over all run blocks. Assert that STEP_SUMMARY writes never reference team_id/profile_uuid.

### P3-2 Cleanup omits the exported IPA and DerivedData
packlab-capture-signed-ipa.yml:419 removes signing, verify and xcarchive. It does not remove RUNNER_TEMP/packlab-signed-export (the IPA with embedded profile) or RUNNER_TEMP/packlab-capture-archive-derived-data, which may hold embedded.mobileprovision copies. This is harmless on ephemeral hosted runners. It is a leak on any future self-hosted runner.
Fix: add both to the rm -rf.

### P3-3 Keychain stays unlocked while third-party code and upload actions run
SPM NextLevel builds and the two upload-artifact steps (lines 386-402) execute while the private key is in the user search list. All of these are pinned and reviewed, so the residual risk is low.
Optional fix: delete the keychain in its own step right after "Verify exported IPA" (keep the always() cleanup as backstop).

### P3-4 The export method is not re-validated inside the script
Line 196 takes method from argv. Any value other than "debugging" becomes Apple Distribution and is written to the ExportOptions method. GitHub enforces choice options for dispatch, and only write users can dispatch, so the impact is nil.
Fix (one line): raise SystemExit unless method is in {"release-testing", "debugging"}.

### P3-5 SIGNED in the sidecar is self-asserted
tools/ci/ios_artifact_provenance.py:16-21,119: anyone running prepare locally with env vars can label any file ios_signed_ipa/SIGNED. The tool hashes; it does not verify signatures. No current consumer trusts it (see the release-manifest note above), so this is not a hole today.

Cheap hardening for ios_signed_ipa:
- require event_name == workflow_dispatch;
- require product_name to end with .ipa;
- require workflow_name == "PackLab Capture Signed IPA";
- require artifact_file_count == 1.

Document in the PL-0358 doc that sidecar SIGNED means "workflow-asserted after codesign verify", not SIGNED_VERIFIED.

### P3-6 Process-list exposure and environment preconditions (documented, accepted)
- security import -P with the password (line 235) and the keychain password (lines 231, 233, 236) are in argv. This is acceptable on single-tenant hosted runners and is documented.
- The in-file main-ref check is not a boundary, because a write user can dispatch an edited copy from another branch. The real boundary is the ios-signing deployment-branch policy (main only) plus required reviewer, plus NOT using repo-level secrets. The doc states all three.
- The owner must create the environment before the first dispatch, otherwise GitHub auto-creates an unprotected environment (documented).
- Opting in to the IPA upload on a public repo exposes UDIDs, team, and the cert CN to any signed-in user for 1 day. The doc warns about this; recommend keeping it off permanently.

## Licensing
- No new dependencies.
- The pinned actions are unchanged from accepted workflows (MIT).
- NextLevel 0.19.1 (MIT) is unchanged and its pin is enforced.
- No OCP/OCCT/Qt/OpenMVS or model-checkpoint surface is touched.
- No secrets, signing material, private scans or supplier data are in the diff. The data-safety guard passes.

## Verdict
SOFTWARE_PASS_WITH_NOTES. The PL-0358 external half is EXTERNAL_PENDING (Apple credentials, protected ios-signing environment, hosted signed run, log review).

Fix P2-1 before any credentialed dispatch on this public repo. P3-1 and P3-2 are recommended in the same change. The task must stay unchecked until the real signed run evidence and a separate log review exist.
