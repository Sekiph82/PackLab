# PackLab Codex Log Contract

## Required metadata

Every `CODEX_LOG_VNN.md` records, without predeclaring a future log commit:

- cycle ID and permanent task ID;
- full GitHub URL for the active Codex prompt;
- full GitHub URL for the matching ChatGPT criteria;
- synchronized child/task starting commit and synchronization result;
- implementation/evidence commit; and
- the exact handoff state permitted by the active prompt.

The log may link its own full GitHub URL, but it must not claim the SHA of the
future commit that will contain that same log. ChatGPT can record the final
log-containing head later in its independent audit.

## Inputs and change set

Record the full paths/URLs of authority and evidence files read, including the
tracker, agent rules, active prompt, criteria, applicable protocol/policy, and
relevant source/artifacts. Record every file changed, added, or deleted and
distinguish product files from evidence logs. State protected files reviewed
and intentionally unchanged.

## Validation records

For every required test or check, record:

1. the exact command or inspection;
2. expected result;
3. explicit failure condition;
4. actual result and exit status when available; and
5. affected criterion or scope.

Record `git diff --check`, protected `TASKS.md` diff review, synchronization,
changed-file review, and remote visibility individually when the prompt
requires them. A green aggregate count cannot replace a prompt-mandated
command. Include negative, boundary, regression, and test-sensitivity
evidence when applicable.

## Failure, privacy, and scope chronology

Record failures and fixes in order, including false-positive validation logic,
environment limitations, warnings that affect interpretation, and any
revalidation. Do not silently rewrite history or omit a failed first attempt.

The log must include a secrets/privacy review and scope review. Never publish
credentials, tokens, signing/private material, private Kenya scans, supplier
documents, proprietary artwork, local environments, caches, or unsafe
generated reconstruction intermediates. Use redaction and placeholders from
`docs/security/SECRETS_POLICY.md`.

## Remote evidence and limitations

Record push success, the remote branch/ref, and a fresh visibility/freshness
check. Record known limitations, unverified assumptions, blocked external
tools, unavailable devices/accounts, physical evidence boundaries, and work
that was not independently rerun. Builder evidence remains E1/E2, not E3.

## Handoff states

For a normal single-task pass, the log ends with `AWAITING_AUDIT`. For a
child within an explicitly authorized milestone batch, it ends with
`READY_FOR_INDEPENDENT_AUDIT`. The matching master log ends with
`AWAITING_MILESTONE_AUDIT`. These are handoffs, not `AUDITED_PASS` and not
task closure.

## Template boundary

`coordination/CODEX_LOG_TEMPLATE.md` remains a helper evidence template. It is
not live project state and cannot replace the exact versioned log required by
the active prompt. Root `TASKS.md` remains the sole live task tracker; a log
must not create a competing current-task ledger.
