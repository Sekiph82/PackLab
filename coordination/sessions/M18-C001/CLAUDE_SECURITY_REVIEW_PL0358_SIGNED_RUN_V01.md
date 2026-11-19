# PL-0358 - independent review of the first credentialed signed run (V01)

Reviewer: Claude security/license reviewer (non-implementing, read-only).
Run: https://github.com/Sekiph82/PackLab/actions/runs/44579021879

No repo edits, no git writes, no dispatch, no settings changed.
- Log saved to the reviewer scratchpad and scanned with count/hash-only output; no matched value was printed.
- Only the provenance sidecar was downloaded. The IPA was NOT downloaded.

## 1. Run identity
- Workflow "PackLab Capture Signed IPA", event workflow_dispatch, branch main, head SHA 8cf1520aad24ce6a7f0f25c1f73f40ff9fe84393.
- Run status completed, conclusion success.
- 8cf1520a is an ancestor of origin/main. The workflow, tests and provenance tool in the working tree are identical to 8cf1520a.
- All 14 job steps succeeded, including:
  - Install signing material;
  - Archive and export;
  - Verify exported IPA signature and identity;
  - early keychain delete;
  - provenance prepare/verify;
  - both uploads;
  - the always() cleanup.
- The cleanup emitted "Temporary signing keychain, profile and certificate material removed."

## 2. Gating evidence (read-only API)
- Run approvals: ios-signing approved by the repository owner.
- Environment ios-signing has two protection rules:
  - required_reviewers: the owner;
  - a custom deployment-branch policy limited to the branch main.
- Repository-level Actions secrets: none.
- Environment secrets: names only, exactly the three PACKLAB_IOS_* names. Values were not read.

## 3. Public log review (664 lines)
- "***" occurs 5 times:
  - Check out source: 2 (token and basic auth header, GitHub-managed);
  - Install step env: 3 (the three PACKLAB_IOS_* values).
- Every other PACKLAB_IOS_/TeamIdentifier/ProvisionedDevices/add-mask/mobileprovision/DEVELOPMENT_TEAM hit is echoed workflow script text (variable names, not values). No "***" from the team or UUID masks appears, so those values were never emitted at all.
- Zero hits for:
  - "Apple Distribution:", "Apple Development:", "iPhone Distribution";
  - "-----BEGIN", "MII..." DER base64, any base64 run of 200+ chars, "PRIVATE KEY";
  - new-format UDIDs (8-16 hex);
  - set -x traces.
- Other pattern hits are benign:
  - UUID-shaped hits (19) are only in Set up job/Check out source (runner temp/credential file GUIDs).
  - 40-hex hits are commit SHAs, the NextLevel revision and artifact-name SHAs.
  - The single team-shaped 10-char token is inside the runner-image release tag URL in Set up job.
- The repository owner login appears only as part of the repository path (4x) and the 2 artifact URLs.
- Summary lines printed:
  - Export method: release-testing;
  - Signing material installed (values not logged);
  - Signed IPA SHA-256 346a18b2...;
  - Signing state: SIGNED (codesign --verify --deep --strict PASS);
  - Package.resolved SHA-256 e8d5d526....
- Result: no secret, team ID, certificate common name, profile name/UUID or UDID appears in the public log.

## 4. Artifacts and sidecar
- Two artifacts, both expiring 2026-11-20T18:08Z:
  - packlab-capture-signed-ipa-provenance-8cf1520a (721 bytes);
  - packlab-capture-signed-ipa-8cf1520a (1659050 bytes; owner opt-in, NOT downloaded by this reviewer).
- The sidecar passes _validate_metadata:
  - type ios_signed_ipa, SIGNED, product PackLabCapture.ipa;
  - event workflow_dispatch, exact workflow name;
  - source_commit 8cf1520a, run id 44579021879 attempt 1;
  - Xcode 16.0 (16A242d), iphoneos 18.0;
  - artifact_file_count 1, artifact_byte_length 1676328, tree digest 5b1d3df1....
- The sidecar holds no team ID, UUID, identity, profile name or UDID.
- Digests are not comparable as printed. The summary IPA SHA-256 (346a18b2..., plain file hash) and the sidecar artifact_sha256 (5b1d3df1..., packlab-sorted-path-length-content-sha256-v1 tree digest over name+size+content) differ by design. This reviewer did not download the IPA. The match of the IPA to the sidecar rests on the provenance verify step inside the run (PASS in the log, same digest and byte length) plus the verify the coordinator ran locally.

## 5. Test pin
V02 P3-A is fixed. tests/ci/test_capture_signed_ipa_workflow.py:158-167 requires:
- the first line to be set -euo pipefail;
- exactly one exact line /usr/bin/codesign --verify --deep --strict "$app_path" > /dev/null 2>&1;
- no "||" on any codesign --verify line;
- the command to come before the SIGNED summary echo.

V03 P3-1 (UserData paths) is fixed by test_profile_is_installed_and_removed_in_both_xcode_profile_directories.

## Findings
### P2 (pre-existing, not introduced by PL-0358; follow-up task): sidecar package_resolved_sha256 is not the file SHA-256
- The sidecar field is 6b54bf14.... The real Package.resolved SHA-256 at 8cf1520a is e8d5d526....
  - It matches the git blob content.
  - It matches the run summary.
  - It is what tools/release/offline_release_manifest.py:217 computes.
- I verified that 6b54bf14... = sha256(bytes.fromhex(e8d5d526...)). This is because the workflows fill PACKLAB_PACKAGE_RESOLVED_SHA256 from hashFiles(), which double-hashes.
- The same pattern exists at packlab-capture-macos.yml:246 and :487 and at packlab-capture-signed-ipa.yml:400.
- The value is deterministic and still binds the lock, so this is not a leak. But a release receipt built from any iOS sidecar would fail IOS_PACKAGE_RESOLVED_PROVENANCE_MISMATCH, and the field name misstates its content.
- Fix (separate task):
  - compute the digest with shasum -a 256 in a prior step, as the resolve step already does, and pass it via step output;
  - add a test that rejects hashFiles for that env var.
- Does not block PL-0358.

### P3 (owner action): public IPA artifact
upload_signed_ipa=true was an explicit owner decision. Until expiry at 2026-11-20T18:08Z, any signed-in GitHub user can download an IPA that embeds the team ID, team name, certificate CN and registered device UDIDs. If the IPA is already saved privately, the owner may delete artifact 14559627575 early. Re-runs should keep the default false.

### P3 (evidence wording)
Record both digests in the tracker with their algorithms: plain IPA SHA-256 346a18b2... and sidecar tree digest 5b1d3df1....

## Acceptance criteria verdict for PL-0358 (device install out of scope)
- Real credentials, environment-gated: MET. Owner approval recorded; main-only branch policy plus required reviewer; secrets are environment-scoped only.
- Hosted archive/export of a signed IPA: MET. Run 44579021879 on main 8cf1520a; codesign --verify --deep --strict PASS; bundle/version checks PASS.
- Provenance: MET for artifact integrity (in-run prepare+verify PASS, single-file signed-IPA origin checks). The pre-existing lock-digest double-hash is filed as a separate P2.
- Log review: MET. No sensitive value in the public log.
- Independent reviewer sign-off: this review (security) plus software reviews V01-V03.

VERDICT: PASS. PL-0358 acceptance criteria are met, and it can be marked CLAUDE_PEER_AUDITED_PASS (not historical AUDITED_PASS). Record the P2 lock-digest finding as a separate follow-up. Device installation and factory/public release gates remain open under their own tasks.
