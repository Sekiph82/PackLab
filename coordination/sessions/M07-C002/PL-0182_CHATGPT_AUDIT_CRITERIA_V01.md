# PL-0182 - ChatGPT Audit Criteria V01

Task: **Add reconstruction cancellation that leaves the project recoverable**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0182_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. PL-0181 is validation-green and published before this child begins; live
   tracker authorization remains valid.
2. Cancellation is explicit, idempotent, deterministic, and propagated through
   the existing process/stage/run/job/workspace authorities.
3. Cancelled stages/runs/jobs/workspaces cannot expose successful output or a
   retained-success manifest; no unsafe orphan process or partial success is
   advertised.
4. Cancellation/failure races, repeated cancellation, missing process, and
   failure-injection paths are tested and normalized truthfully.
5. RAW_CAPTURE/source bytes, accepted evidence retention, provenance and
   workspace isolation remain intact; retry uses a new safe revision and does
   not reuse stale output identity.
6. No unrelated job behavior, schema/dependency, UI-owned truth, PL-0183/M08
   code, native/physical claim, or unauthorized scope is included.
7. Required focused/full/static/security/scope checks and child log evidence
   pass truthfully, with the exact `READY_FOR_INDEPENDENT_AUDIT` handoff.
