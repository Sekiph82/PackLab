# PL-0361 - Codex Peer Review V01

Task: **Publish build artifacts with clear signed/unsigned provenance**  
Review type: Independent source, workflow, test and security review  
Review status: **PASS**

## Scope inspected

The reviewers inspected the committed provenance helper, macOS workflow,
artifact-upload guard tests, offline changelog path correction, and OwnerDev
runtime-manifest test scope. Reviewers checked the source and the actual hosted
run evidence rather than relying on the implementation summary.

## Findings and resolutions

- The workflow path filters did not include the new provenance helper. Added
  `tools/ci/ios_artifact_provenance.py` to both pull-request and `main` push
  filters; the subsequent `main` push triggered the macOS workflow.
- The new helper and tests were added to the repository contract checks.
- Tests now cover deterministic tree hashing, tamper detection, exact sidecar
  fields, mismatched signing state, unsupported signed IPA metadata, invalid
  workflow names, empty products, digest/length/file-count mismatches,
  symlink rejection, and junction rejection.
- The XCTest failure-artifact upload now has an immediately preceding bounded
  input guard and requires a successful guard outcome. Missing diagnostics
  fail closed. The generated SPM resolution upload no longer overrides job
  status and now requires its validated lockfile.
- Two pre-existing Windows quality failures were repaired: the OwnerDev path
  test no longer scans the safe-sync orchestration helper as a runtime
  manifest, and offline changelog validation uses canonical resolved paths.
- Signed IPA provenance is deliberately unsupported in the helper until the
  separate PL-0358 signing path and actual signature/profile checks are
  available. No signed IPA was produced or represented as signed.

## Review conclusions

- Source/workflow reviewer: **PASS**; both published products are rehashed
  immediately before upload, and the upload path includes the corresponding
  sidecar.
- Tester: **PASS**; focused and repository test results are recorded in the
  execution log.
- Security reviewer: **PASS**; metadata uses a strict allowlist, roots and
  descendants reject symlinks/junctions, the action references remain pinned,
  workflow permissions remain `contents: read`, and artifact retention remains
  one day.
- No signing credentials, keychains, certificates, provisioning profiles,
  personal identifiers, private scans, supplier files, or new dependencies
  were added or read.

This peer review is implementation evidence. It is not an independent ChatGPT
audit, physical-device acceptance, signing acceptance, or release approval.
