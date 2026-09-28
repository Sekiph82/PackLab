# PL-0175 - ChatGPT Audit Criteria V01

Task: **Implement the OpenMVS dense point-cloud stage**

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CHATGPT_AUDIT_V03.md

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CODEX_PROMPT_V01.md

All criteria below are mandatory for closure of PL-0175.

1. Root `TASKS.md` authorizes M07-C001 / `READY` / `CODEX` for PL-0175
   before material work; PL-0174 remains `AUDITED_PASS`, PL-0068 remains
   `OWNER_REQUIRED`, and PL-0176+ remains unauthorized.
2. The implementation is limited to the bounded dense-stage adapter, its
   public tests, and the matching log; accepted PL-0166 through PL-0174
   behavior is not rewritten.
3. The public request binds one accepted `OpenMVSSceneConversionPlan` to safe
   relative input/output identities, source/plan/configuration digests, the
   OpenMVS `2.4.0` pin, and the reconstruction authority/scale boundary.
4. The adapter requires an explicit already-probed dense executable, validates
   engine identity/version/executable matching, performs no discovery or
   installation, and maps only PackLab-owned semantic fields to the exact
   pinned `DensifyPointCloud` argv.
5. Command construction rejects unsafe paths and unsupported or
   caller-controlled options; public tests assert the complete argv and do
   not merely assert that a command was attempted.
6. Execution uses the existing no-shell process/stage boundary, propagates
   timeout and cancellation, bounds and redacts evidence, and normalizes
   stage identity, status, exit code, and failure reason.
7. Successful, failed, and cancelled public results are mutually consistent;
   failed/cancelled runs expose no successful dense output, and successful
   results preserve exact input/configuration provenance without inferring
   geometry from arbitrary stdout/stderr.
8. The result remains `RECONSTRUCTION_OBSERVATION` with only `RELATIVE` or
   `METRIC_UNVERIFIED` scale; it never claims `METRIC_VERIFIED`, Scan Master,
   CAD, measurement, or engineering authority.
9. Public tests are behavior-sensitive for valid command mapping, invalid
   paths/options, wrong or mismatched probes, non-zero execution, timeout,
   cancellation, output identity, provenance, and regression against the
   accepted conversion and predecessor stage contracts.
10. The exact locked full suite exits 0; unavailable engines, skips, warnings,
    native/physical limitations, and the absence of a host OpenMVS executable
    are reported truthfully without skips or xfails hiding the task.
11. Ruff, format, targeted mypy, compileall, `git diff --check`, protected-
    file/scope, dependency/lock, privacy/secrets/signing, generated/binary,
    and remote-visibility checks pass truthfully; unchanged repository-wide
    mypy debt is disclosed.
12. The matching `PL-0175_CODEX_LOG_V01.md` exists, uses full GitHub URLs,
    records exact commands/results/SHAs/limitations and separate publication
    boundaries, and ends exactly `AWAITING_AUDIT`.
13. No mesh/refinement/texture stage, output-preservation contract,
    orchestration, engine discovery/installation, schema/dependency/lock
    change, tracker or ChatGPT audit artifact edit, physical/native-device
    acceptance, or PL-0176+ implementation is included.

Closure requires a fresh independent ChatGPT audit of the PL-0175
implementation diff, source, tests, and handoff against every criterion.
