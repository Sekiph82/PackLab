# PL-0381 implementation gap — V01

Inspection before runtime edits found that project authority writes had no low-free-space preflight or injected free-space source, and an `ENOSPC` during authority replacement escaped as a raw `OSError`. Existing atomic replacement preserved the prior authority bytes, but the error was not actionable and low-space behavior was not testable without touching the real disk.

The owner has authorized autonomous implementation. PL-0381 now adds an injected `free_space_reader`, a bounded 64 KiB project-write reserve, fail-closed preflight before authority publication, and an actionable `ProjectError` translation for `ENOSPC` at the authority publish boundary. Tests cover injected zero-space and an injected publish-time `ENOSPC`, preserving authority/state/raw bytes. Comprehensive execution remains deferred to the M17 test batch.

The reserve is a conservative guard for one authority JSON write; it is not a guarantee against concurrent disk consumption or failures in later compatibility-mirror writes. The authority remains the recovery source if a later mirror write fails.
