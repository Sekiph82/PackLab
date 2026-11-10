# PL-0370 — Codex Prompt V02

Task: **Create a bounded private local real-packaging reference corpus outside Git**  
Milestone: **M17** · Cycle: **M17-C001**

V02 responds to the advisory M17 source/security findings. It supersedes V01 implementation scope while retaining all prior evidence.

## Required remediation

- Reject YCB archive files and manifest paths that are symlinks/junctions/reparse points or escape the dedicated local dataset root.
- Publish extracted members only after a complete bounded write and size/hash verification; interruption must leave no destination partial.
- Pin the three reviewed archive names, official URLs, exact byte lengths and SHA-256 values. Verify every recorded extracted member's bytes/hash against the named archive member, not only against a self-authored manifest.
- Add regression tests for linked source/destination paths, interrupted extraction cleanup, and archive-member provenance. Tests may skip only where the OS cannot create a symlink fixture; the utility must still reject the link where supported.
- Keep all full source/derived data outside Git, preserve CC BY 4.0 terms, and retain all uncertainty/trademark caveats.

## Validation timing

- The prior grouped M17 test batch has already run twice. Do not start another broad Tester run in this child. Record any new regression test source as not re-executed after remediation; do not close the task until a future authorized consolidated validation covers the final source.
- Re-run the bounded local YCB manifest artifact validator after remediation; it must verify pinned archive identity and every selected source member.
- Write `PL-0370_CODEX_LOG_V02.md`, including earlier failures, fixes, exact command/result, and explicit test limitation.
