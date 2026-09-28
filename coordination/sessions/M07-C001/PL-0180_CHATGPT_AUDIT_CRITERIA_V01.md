# PL-0180 - ChatGPT Audit Criteria V01

Task: **Add CPU/GPU-aware presets and memory-safety limits**

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CHATGPT_AUDIT_V03.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0180_CODEX_PROMPT_V01.md

All criteria below are mandatory for closure of PL-0180 V01.

1. Root `TASKS.md` authorizes PL-0180 V01 with status `READY` and Required
   Actor `CODEX`; PL-0179 remains `AUDITED_PASS`, PL-0068 remains
   `OWNER_REQUIRED`, and PL-0181+ remains unauthorized.
2. The diff is limited to the existing reconstruction-preset resource-policy
   boundary, its public tests, and the matching V01 log. Accepted PL-0166
   through PL-0179 behavior, tracker state, audit artifacts, schemas,
   dependencies, locks, and protected files are preserved.
3. The resource policy is immutable, backend-neutral, versioned, and
   deterministically serialized/digested. Named CPU-safe and GPU-aware
   presets have explicit identities and truthful non-benchmark limitations.
4. Execution mode validation accepts exactly `cpu-only`, `gpu-preferred`, and
   `gpu-required`; invalid values and non-boolean/overflow type confusion fail
   through PackLab-owned errors.
5. GPU selection consumes explicit capability evidence only. Driver labels or
   arbitrary hardware strings do not establish CUDA; `gpu-preferred` records
   a deterministic CPU fallback for unavailable/unknown CUDA, while
   `gpu-required` fails closed.
6. Input, working-set, retained-output, and worker-count limits are positive,
   bounded, immutable integers with coherent relationships. Estimates over a
   limit fail before execution and are never silently clamped or treated as
   advisory.
7. The resolved plan preserves preset identity, policy digest, selected mode,
   capability status/provenance, limits, estimates, and an explicit outcome
   or fallback reason. Equivalent inputs serialize and digest identically.
8. The resource policy is exposed through the existing reconstruction preset
   configuration/provenance view without changing existing component defaults,
   authority limitations, or backend-specific adapter option spelling/order.
9. Public tests are behavior-sensitive through construction, invalid/boundary
   limits, capability states, CPU fallback/GPU-required rejection,
   over-budget estimates, immutability, deterministic serialization, and
   existing preset/reconstruction regressions. Tests must not merely inspect
   constants or mirror private implementation details.
10. The exact locked full suite exits `0`; no new skip/xfail hides a finding,
    and unavailable `cv2`, symlink privilege, warnings, and absent OpenMVS
    executable are reported truthfully.
11. Ruff, format, targeted mypy, compileall, diff, protected-file/scope,
    dependency/lock, privacy/secrets/signing, generated/binary, and
    remote-visibility checks pass truthfully; unchanged repository-wide mypy
    debt is disclosed.
12. `PL-0180_CODEX_LOG_V01.md` uses full GitHub URLs, records exact commands,
    results, SHAs, limitations, scope, separate publication boundaries, and
    ends exactly `AWAITING_AUDIT`.
13. No process launch, engine discovery/installation/download, engine-specific
    CLI passthrough, orchestration, output retention/cancellation change,
    schema/dependency/lock change, tracker or ChatGPT-audit edit by Codex,
    generated/private artifact, physical/native-device acceptance, or
    PL-0181+ implementation is included.

Closure requires a fresh independent ChatGPT audit of the V01 diff, source,
tests, and handoff against every criterion.
