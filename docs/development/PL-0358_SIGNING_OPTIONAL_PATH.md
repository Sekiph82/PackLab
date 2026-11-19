# PL-0358 - Optional secret-safe signed IPA path

Status: software half implemented. **EXTERNAL_PENDING_APPLE_SIGNING_CREDENTIALS**.
No signed IPA has been produced. No secret was read, created or requested, and no
GitHub setting or environment was changed.

## Shape

| Path | Workflow | Trigger | Secrets |
| --- | --- | --- | --- |
| Unsigned simulator app + device archive (default) | `.github/workflows/packlab-capture-macos.yml` | push, pull_request, dispatch | none |
| Optional signed IPA | `.github/workflows/packlab-capture-signed-ipa.yml` | `workflow_dispatch` on `main` only | `ios-signing` environment only |

The signed job:

1. Checks secret *presence* as booleans (`secrets.X != ''`); no value enters that step.
   All three absent: summary `SKIPPED_CREDENTIALS_ABSENT`, job succeeds, nothing is built.
   Some absent: job fails (misconfiguration).
2. Decodes the certificate and profile into a `umask 077` runner temp directory.
   It validates that the profile covers `<TEAM>.com.packlab.capture`, is not
   expired, is not enterprise, and that `get-task-allow` matches the export method.
   The team ID and profile UUID are masked with `add-mask`.
3. Imports the certificate into a temporary keychain with a random password
   (`openssl rand`). Access is limited to `codesign`/`security` (no `-A`). The
   `.p12` is deleted right after import.
4. Applies manual signing only to the PackLabCapture Release configuration,
   runner-local. SPM targets are not touched. It then archives and exports with a
   generated `ExportOptions.plist`. Xcode output is never printed: Actions logs on this
   public repo are world-readable, and Xcode signing errors name the certificate
   (often the owner's personal name), the profile and the team. On failure the job
   prints only the count of `error:` lines. To diagnose, reproduce locally on a Mac.
5. Verifies the IPA with `codesign --verify --deep --strict`, checks for
   `embedded.mobileprovision`, and checks bundle ID, version and build. Then it
   deletes the keychain and installed profile immediately, before any upload step.
6. Writes a `tools/ci/ios_artifact_provenance.py` sidecar with
   `artifact_type=ios_signed_ipa` and `signing_state=SIGNED`. The sidecar holds no
   team ID, profile or identity. The tool accepts `ios_signed_ipa` only for a single
   `.ipa` file from a `workflow_dispatch` run of "PackLab Capture Signed IPA".
   **Sidecar `SIGNED` is workflow-asserted after `codesign` verification. It is not
   `SIGNED_VERIFIED`.** The tool hashes the file; it does not check signatures, and
   anyone can run it locally. The release manifest
   (`tools/release/offline_release_manifest.py`) requires a separate signature-evidence
   document before it accepts `SIGNED_VERIFIED`.
7. Uploads the sidecar (1 day). It uploads the IPA only if the dispatcher sets
   `upload_signed_ipa=true` (1 day). The repo is public, and a signed IPA embeds the
   provisioning profile: team ID, team name, certificate name and device UDIDs.
   **Recommendation: keep it off permanently.** Install the IPA by a private route,
   such as Xcode on a Mac or an organisation-private distribution channel.
8. Runs an `always()` cleanup that deletes the keychain, the installed profile, the
   signing directory, the signed archive, the export directory and DerivedData.

`tests/ci/test_capture_signed_ipa_workflow.py` locks these properties in.

## What the owner must configure

1. Apple Developer Program membership (a paid team; Personal Team profiles expire
   after 7 days and cannot be exported from CI usefully).
2. Register the App ID `com.packlab.capture` (or change the bundle ID in a separate
   task) and register the iPhone 16 UDID.
3. Create an **Apple Distribution** certificate and an **Ad Hoc** profile (export method
   `release-testing`). Alternatively, create an **Apple Development** certificate and a
   **Development** profile (export method `debugging`). Export the certificate and private
   key as a password-protected `.p12`. Keep both files off this repository and off
   the Desktop working tree.
4. GitHub > Settings > Environments > create `ios-signing` **before** any dispatch:
   - Required reviewers: the owner (prevent self-review stays off for a single owner).
   - Deployment branches and tags: selected branches, `main` only.
   - Environment secrets (names must match exactly):
     - `PACKLAB_IOS_CERTIFICATE_P12_BASE64` (base64 of the `.p12`)
     - `PACKLAB_IOS_CERTIFICATE_PASSWORD` (the `.p12` password)
     - `PACKLAB_IOS_PROVISIONING_PROFILE_BASE64` (base64 of the `.mobileprovision`)
   - Do **not** add these as repository-level secrets. Repository secrets are visible
     to every workflow; environment secrets are released only after reviewer approval.
5. Dispatch "PackLab Capture Signed IPA" from `main` and approve the environment
   deployment.

## Evidence needed to close PL-0358

- Hosted run URL on an exact `main` SHA: environment approval recorded, steps green,
  summary showing `SIGNED (codesign --verify --deep --strict PASS)` and the IPA SHA-256.
- Downloaded provenance sidecar that passes
  `python tools/ci/ios_artifact_provenance.py verify` against the downloaded IPA,
  if one was uploaded.
- Log review confirming no secret, team ID or profile UUID appears unmasked, and
  cleanup step success.
- Separate reviewer sign-off. Installing on the physical iPhone 16 belongs to the
  device tasks, not to this one.

## Residual risks (unvalidated until the first hosted run)

- `PROVISIONING_PROFILE_SPECIFIER` is set to the profile UUID. If Xcode 16.0 rejects
  that, switch to the profile `Name`, validated and quoted.
- `release-testing`/`debugging` are the Xcode 15.4+ names for ad-hoc/development.
- The `.p12` password is passed to `security import -P`, which makes it briefly
  visible in the process list. That is acceptable on a single-tenant ephemeral
  hosted runner, but not on a shared self-hosted runner.
- The `main` check inside the workflow is not a security boundary. A user with write
  access could dispatch an edited copy from another branch. The real boundary is the
  `ios-signing` deployment-branch policy (`main` only), plus the required reviewer,
  plus keeping the secrets out of repository-level secrets.
- Dispatching before `ios-signing` exists makes GitHub auto-create an unprotected
  environment. It has no secrets, so the job only skips, but the owner should still
  add protection.
