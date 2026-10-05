# PL-0338 - ChatGPT Audit Criteria V01

Task: **Audit trail for asset metadata edits**

All criteria are mandatory.

1. Append-only hash/integrity chained audit event contract exists.
2. Events bind actor/reason/time/state revision/operation/targets/before-after revision IDs.
3. Optimistic expected-state revision prevents stale edits; state+event publication is atomic.
4. Replay detects tamper, reorder, deletion/disconnection and duplicate event IDs.
5. Audit payload excludes attachment bytes, secrets and ambient paths.
6. Tests cover create/update/link/unlink events, stale writers, corruption and deterministic validation.

7. Scope remains inside PL-0338 and accepted predecessor seams; no later-child/M16+ implementation.
8. Focused/full/static/security/dependency/remote evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0338_CODEX_PROMPT_V01.md
