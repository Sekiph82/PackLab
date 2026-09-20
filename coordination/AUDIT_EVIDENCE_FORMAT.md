# PackLab Audit Evidence Format

## Evidence-record contract

An evidence record is tied to one frozen requirement and contains:

| Field | Required meaning |
| --- | --- |
| Criterion/task reference | Permanent PL ID, cycle/version, and exact numbered criterion or master criterion. |
| Evidence level | `E1`, `E2`, `E3`, or `E4` with the applicable ownership boundary. |
| Source/command | Full GitHub URL, file path, commit/diff, or exact command that produced the evidence. |
| Expected result | The observable result required for the criterion to pass. |
| Failure condition | The result that blocks or fails the criterion. |
| Actual result | What was actually observed, including exit status or a concise redacted output summary. |
| Disposition | `PASS`, `FAIL`, `CHANGES_REQUIRED`, `BLOCKED`, `OWNER_REQUIRED`, or `NOT_INDEPENDENTLY_VERIFIED`, assigned only by the authorized auditor where applicable. |

Evidence records should be concise enough to audit, but must preserve the
context needed to reproduce or challenge the conclusion. One aggregate test
count must not stand in for missing criterion-level records.

## Commands and output

Record the exact command, working-repository context, relevant start/current
commit, expected result, failure condition, actual result, and whether the
command was run by Codex or ChatGPT. Include exit status when available.
Summarize output to the material lines and redact secrets, private paths,
tokens, signing material, personal identifiers, supplier data, and private
Kenya scan references. Never paste an unreviewed terminal dump into a public
log or audit. If safe redaction cannot be guaranteed, record the command
class, result, and a redacted reference instead.

## Files, diffs, and commits

For inspected files, record the full repository-relative path, relevant
one-based line or section location, and the reason it matters. Record the
commit SHA, parent/range, branch/ref, and full GitHub URL for important source,
diff, artifact, prompt, criteria, log, or audit evidence. For a new file,
make the content visible with an intent-to-add/staged diff or inspect the
committed GitHub diff; an empty plain diff of an untracked file is not proof
of review.

A file list must distinguish product/source artifacts, evidence logs, and
protected or intentionally unchanged files. Do not imply that a later log
commit was part of an earlier implementation commit.

## Evidence levels

- **E1 — builder check:** Codex-run observation or command with limited
  reproducibility context.
- **E2 — reproducible builder evidence:** exact command, start/current commit,
  expected result, failure condition, actual result, and affected scope.
- **E3 — independent audit evidence:** ChatGPT’s own GitHub inspection,
  independent rerun, or independent reasoning against frozen criteria.
- **E4 — owner/physical evidence:** owner-controlled product, account, device,
  physical measurement, or decision that must not be fabricated by AI.

Builder E1/E2 records remain builder evidence even when complete. They do not
become E3 because a log repeats them. Unrerun runtime, device, physical,
signing, or external-tool evidence is labeled with its limitation.

## Negative, regression, and test-sensitivity evidence

When relevant, record invalid, missing, unsupported, interrupted, corrupt,
boundary, privacy, and failure-path results, including the expected safe
diagnostic or rejection. Record regression checks for required earlier
behavior. Record why a test would fail if the intended behavior were broken;
avoid tests that only mirror implementation details or assert a value produced
by the same unverified assumption.

## Residual risk and limitation fields

Each material evidence set records:

- residual risk after the observed result;
- known limitation or unverified assumption;
- dependency, device, physical, account, or owner gate;
- whether a future task or ADR is required; and
- the next evidence needed, without turning that suggestion into current task
  authorization.

Do not convert a limitation into a pass claim or silently omit it because the
main path is green.

## Privacy and security redaction

Never publish credentials, tokens, private keys, provisioning material,
session data, secret-bearing config, private scans, supplier documents,
proprietary artwork, or identifying private paths. Use unmistakable
placeholders such as `<PACKLAB_TEST_TOKEN_REDACTED>` and omit sensitive output
when a placeholder is not sufficient. Record only that the review occurred,
the redacted incident/reference, and the resulting disposition. See
`docs/security/SECRETS_POLICY.md` for the protected-data response.

## Child and milestone indexing

Child evidence is indexed by permanent task ID and cycle/version, with links
to the full prompt, criteria, implementation/evidence commit, child log, and
audit. A milestone index additionally records frozen order, freshness checks,
child boundaries, stop frontier, remote visibility, and the master log. Child
records are not replaced by a milestone summary, and a milestone execution
batch is not an acceptance batch.

## Non-tracker boundary

This format defines how evidence is recorded. It is not a current-task,
progress, actor, or closure tracker. Root `TASKS.md` remains the sole live
project-status surface, and only the authorized lifecycle owner updates it.
