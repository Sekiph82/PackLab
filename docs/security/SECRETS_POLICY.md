# PackLab Secrets and Protected-Data Policy

## Purpose and boundary

This policy defines what must never enter PackLab’s public Git history and
how builders respond when exposure is suspected. It is a governance contract,
not a signing system, credential store, CI implementation, keychain
integration, or concrete ignore-file configuration.

## Secret classes

Treat all of the following as secrets unless an approved security review
explicitly classifies a specific public artifact otherwise:

- GitHub tokens, API tokens, webhook secrets, session cookies, refresh tokens,
  SSH private keys, and other repository/service credentials;
- Apple IDs used for development or distribution, App Store Connect/API keys,
  authentication/session data, and related recovery material;
- signing private keys, private key containers, certificate private material,
  and passwords or passphrases that unlock them;
- provisioning profiles or entitlements containing device, team, or
  distribution-sensitive material;
- passwords, database credentials, encryption keys, recovery codes, and
  personal access credentials; and
- cloud-provider credentials, service-account keys, storage signatures, and
  temporary cloud session credentials.

Public certificate material may identify a signer or permit signature
verification, but it is not equivalent to the private signing key. Public
certificates may be published only when their provenance and intended public
use are approved. Private signing keys, key containers, provisioning-sensitive
material, and associated passwords remain protected even when a matching
certificate is public.

## Prohibited locations

Secrets must not appear in Git history, tracked configuration, source, logs,
screenshots, fixtures, prompts copied into the repository, generated
artifacts, examples, issue text, or documentation. A secret is still exposed
if it is placed in a deleted file, an earlier commit, a build output, or an
image. Do not use a real-looking token as an example.

Private Kenya scans, supplier documents, proprietary artwork, unreleased
capture evidence, and other owner-confidential production data are protected
data even when they are not credentials. They must not enter the public repo,
logs, screenshots, fixtures, prompts, or generated outputs without explicit
authorization and a separately audited public-data decision.

## Safe handling principles

Concrete storage and CI integrations are future work. Their governing
principles are:

1. Environment variables may supply short-lived values to a process without
   committing the value, but commands, crash dumps, child-process output, and
   logs must not echo it. Prefer least privilege and scoped, short-lived
   credentials.
2. An operating-system keychain or equivalent protected secret store may be
   used by a future authorized implementation. The keychain name, lookup
   metadata, and redacted status may be documented; the secret value must not.
3. CI secrets belong in the CI provider’s protected secret facility with
   minimum repository/environment scope, masked output, rotation, and an
   explicit workflow permission boundary. This policy does not implement CI
   secret plumbing.
4. Local `.env` files and credential-bearing config are local-only inputs. Use
   a public template containing safe placeholders, keep real values outside
   tracked paths, and defer concrete `.gitignore` changes to PL-0021.
5. Never copy a credential into a prompt, test fixture, diagnostic command,
   screenshot, generated report, or Codex log for convenience.

## Public-safe placeholders

Examples use an unmistakable, non-credential syntax such as:

```text
<PACKLAB_TEST_TOKEN_REDACTED>
<APPLE_KEY_ID_EXAMPLE_ONLY>
<CLOUD_CREDENTIAL_NOT_A_SECRET>
```

Placeholders must contain an explicit `EXAMPLE`, `TEST`, or `REDACTED` marker,
angle brackets, and no valid token-shaped value. Do not reuse a real prefix,
suffix, length, checksum, or partially redacted credential that could be
confused with a live secret.

## Accidental exposure response

If a secret or protected private data is found, stop the affected work and do
not continue publishing around it. The responsible actor must:

1. record only a redacted incident reference;
2. revoke or rotate the exposed credential through its owner/provider;
3. identify affected branches, commits, logs, artifacts, caches, screenshots,
   and external copies;
4. preserve the evidence needed for the security review; and
5. use the approved repository/history purge process after rotation and
   authorization. Merely deleting the latest file is insufficient because the
   value may remain in Git history, forks, caches, or logs.

The incident must remain visible to the appropriate owner/auditor as a
security finding without embedding the secret itself. Publication resumes only
after the authorized response confirms the affected history and downstream
copies have been handled.

## Redaction for evidence

Codex logs and ChatGPT audits may record that a secret scan or protected-data
review occurred, the tool class used, the result, and a redacted incident ID.
They must not record values, token prefixes/suffixes, private-key blocks,
session cookies, personal identifiers, private paths that reveal protected
locations, or screenshots containing secrets. Replace sensitive values with a
placeholder such as `<PACKLAB_TEST_TOKEN_REDACTED>` and omit command output
when redaction cannot be guaranteed.

## Explicit non-implementation boundary

This task does not implement Apple signing, provisioning, CI secret wiring,
OS-keychain integration, credential storage, secret scanning automation, or
the concrete `.gitignore` policy deferred to PL-0021. Those systems require
their own authorized scope and evidence.

## Cross-references

This policy operates with `AGENTS.md`, `coordination/AUDIT_POLICY.md`, and the
source-control rules in `docs/architecture/SOURCE_CONTROL_POLICY.md`. Root
`TASKS.md` remains the sole live project-status tracker.
