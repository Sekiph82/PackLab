# PL-0080 — Codex Remediation Log V02

- Authorization: M03-BATCH-002 / READY / CODEX; PL-0070 accepted; PL-0068 OWNER_REQUIRED; no M04 work.
- Prompt/criteria/prior audit read: PL-0080 V02/V02/V01.
- Implementation commit: `f5eb2f5` (`fix(PL-0080): sample and bind AR frame poses`).

The shared ARSession owner now consumes `ARFrame` updates, records the monotonic ARKit timestamp and raw camera-to-world 4x4 transform into a bounded `PoseBuffer`, and exposes nearest eligible pose binding for accepted capture timestamps. Transform size/finiteness, normal tracking, stale tolerance, missing data, and out-of-order samples are explicit; source timebase and row-major copying semantics are documented.

Validation:

- `git diff --check`: passed.
- `$env:PYTHONPATH=(Join-Path (Get-Location) 'core/src'); python -m pytest -q`: `162 passed, 4 skipped, 1 deselected, 1 warning`.
- Native ARKit/iPhone execution is unavailable on this Windows workspace and is not claimed.
- No TASKS/audit edits, secrets, private assets, caches, or signing material.

Prior findings addressed: real ARFrame sampling, explicit timebase/transform validation, bounded buffer, accepted-capture binding, and required boundary tests. Independent Apple-host evidence remains for audit.

READY_FOR_INDEPENDENT_AUDIT
