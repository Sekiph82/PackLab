# PL-0360 - Codex Peer Review V01

Task: **Prevent Apple signing material in public repo**
Review type: Independent source, test and security review
Review status: **PASS**

## Scope inspected

Reviewers inspected the actual PL-0360 source changes, dedicated and existing
CI workflow changes, exact-path/hash documentation-marker allowlist, policy
documentation, `.gitignore` additions, and synthetic negative tests. The
review was independent of the implementation summary.

## Review findings and resolution

- Common Apple signing export names, including certificate and provisioning
  profile base64 variables, needed explicit coverage. The scanner patterns
  and synthetic canaries now cover these names.
- The public-document marker exception needed stronger bounds. Suppression now
  requires the exact path and SHA-256 digest to match both the JSON manifest
  and a two-entry source-pinned map. Only inline prose markers can be
  suppressed. Header-only lines, an END marker, or a base64-like payload after
  the header remain blocked. Regression tests cover changed hashes, full
  synthetic blocks, inline payloads, and paths outside the documented areas.
- The allowlist loader now rejects non-object JSON roots and malformed entries
  with a redacted, fail-closed scan result; a malformed-root regression test
  covers the stable schema error.
- The first hosted scan exposed Windows/Linux line-ending drift in Markdown
  digests. Hashing now canonicalizes CRLF to LF, and a CRLF regression fixture
  verifies the same reviewed digest is accepted.
- Repository-wide Ruff exposed an existing `UP012` lint error in the offline
  version inventory tests. Its redundant UTF-8 encoding argument was removed
  without changing test semantics.
- The first full Windows suite exposed a path-spelling mismatch for temporary
  paths. The scanner now computes its repository-relative path from the
  resolved file path, and a Windows case-alias regression covers the behavior.

## Review conclusions

- The dedicated workflow runs for every pull request and push to `main`, uses
  read-only repository permissions, and pins its checkout and Python setup
  actions. It receives no signing credentials.
- The Windows quality workflow also runs the signing-material check.
- Diagnostics contain finding codes only; they do not print paths, matched
  values, or file contents.
- No real certificate, profile, key, keychain, credential, or unreviewed
  dependency was added. Test canaries are synthetic.
- The current tracked public repository passes the signing-material scan.

Tester review: **PASS**, 16 focused tests and both repository guard commands
passed.

Source/workflow review: **PASS** after the final source-pinned allowlist and
common-export coverage changes.

Security review: **PASS** after the final allowlist hardening.

This peer review is implementation evidence. It is not an independent
ChatGPT audit, hosted verification, signing acceptance, physical-device
acceptance, or release approval.
