# PackLab Independent Review and Audit Policy (2026-11-10)

## Authority
For new work, **Claude Code** is the owner-authorized sole executor and `TASKS.md` lifecycle writer. Root `TASKS.md` is the only live project-status tracker. Historical `CHATGPT_AUDIT_*.md`, `CODEX_PEER_REVIEW_*.md`, frozen prompts and previous accepted commits are immutable evidence. Claude may create `CLAUDE_PEER_REVIEW_*.md` records but may not misrepresent them as earlier ChatGPT audits.

## Real evidence hierarchy
- **E0:** assertion with no observed proof, never sufficient.
- **E1:** builder statement/command without reproducible context.
- **E2:** actual reproducible command/test with source SHA, expected/fail/actual and output or link.
- **E3-auto:** independently inspected diff/source/tests/CI by a non-implementing Claude subagent; explicitly labeled `CLAUDE_PEER_REVIEW`, not historical ChatGPT E3.
- **E4:** owner-controlled physical, device, account, external factory or formal legal evidence; not synthesizable or replaced by E3-auto.

## Acceptance
A new `[x] CLAUDE_PEER_AUDITED_PASS` requires: original task's mandatory acceptance criteria satisfied, relevant direct tests actually run, negative/boundary/regression cases, separate reviewer inspection, security/licensing/supplier/privacy review, exact changed-file and commit scope, CI outcomes when mandatory, reproducible signed/unsigned distinction, and source/remote/local synchronization disclosure. Documentation-only tasks require appropriate document validation and review; they do not imply integrated software or production acceptance.

Subagent reviewer must inspect actual base/head diff and evidence; builder-only review is NOT independent. If separate review unavailable: `[ ] IMPLEMENTED_REVIEW_PENDING`. If a test fails or a material finding persists: `[ ] CHANGES_REQUIRED` with exact correction, then retry same PL ID. Do not lower acceptance criteria, rewrite audit history or skip dependent requirements to secure a pass.

## External gates and progression
An unavailable factory, real printer, physical artifact, iPhone verification, Apple signing credential, legal decision or external service must be recorded as `[ ] EXTERNAL_PENDING_<reason>`, with exact missing evidence and dependent tasks. Claude may advance to other dependency-independent tasks. Synthetic/public proxy ground truth is valid only for synthetic software tests, not observed physical millimetre accuracy or factory release.

## Continuous audit
Use append-only versioned `coordination/sessions/` logs and peer-review artifacts for each PL ID, plus consolidated milestone reviews when useful to optimize tokens. A task must not be marked accepted until the mandatory review/test evidence for that task is actually present. Root tracker updates must match source truth. Preserve technical authority (PackScan, Scan Master, Design Model), commercial licenses, security, public-repository privacy and real-world approval requirements.
