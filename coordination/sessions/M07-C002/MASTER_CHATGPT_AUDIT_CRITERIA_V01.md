# M07-C002 - Master ChatGPT Audit Criteria V01

Milestone: **M07 - Reconstruction Backends & Photogrammetry**
Scope: **PL-0181 through PL-0183**
All criteria are mandatory.

1. Root `TASKS.md` explicitly authorizes `M07-C002 / READY / CODEX` for this
   exact master batch before material work; PL-0180 is `AUDITED_PASS`, PL-0068
   remains `OWNER_REQUIRED`, and M08 remains unauthorized.
2. The package contains the master prompt, this master criteria file, the
   repository-required master-log template, and one prompt/criteria/log path
   for each ordered child PL-0181, PL-0182, and PL-0183.
3. Codex executes exactly PL-0181, then PL-0182, then PL-0183; each child has
   a distinct implementation/evidence commit, log-only commit, and
   `READY_FOR_INDEPENDENT_AUDIT` handoff. A failed or blocked child stops the
   batch frontier and does not authorize later children.
4. PL-0181 creates one PackLab-owned public orchestration boundary for the
   existing COLMAP/OpenMVS stage contracts in the required order, with explicit
   inputs, preset/configuration provenance, stage results, output manifest,
   and fail-closed handling for missing capabilities, invalid dependencies,
   failed stages, cancelled stages, and missing outputs. It reuses existing
   backend, workspace, job, process, provenance, and evidence authorities.
5. PL-0181 does not silently install/download engines, bypass probes, expose
   engine-specific flags as domain truth, mutate RAW_CAPTURE, publish partial
   success as complete, or introduce UI-owned reconstruction logic.
6. PL-0182 makes cancellation explicit, idempotent, and recoverable across the
   orchestration/process/job/workspace boundary. A cancelled run must produce
   coherent cancelled stage/job/workspace state, no successful output manifest
   or retained success artifact, preserve source bytes, avoid unsafe orphaned
   process state, and permit a later retry in a new safe reconstruction
   revision. Cancellation/failure races and repeated cancellation are covered.
7. PL-0183 converts or publishes a successful final textured-mesh result only
   through PackLab-supported formats already bounded by the repository
   contract, with deterministic format/configuration/provenance and atomic
   derived-output publication. It rejects malformed/failed/cancelled inputs,
   unsafe destinations, unsupported formats, collisions/ambiguous overwrite,
   and source/output identity aliasing. RAW_CAPTURE and the master source are
   never overwritten; output remains reconstruction observation, not Scan
   Master, metric, CAD, or engineering authority.
8. All three children preserve accepted M07 predecessor contracts, including
   camera/prior provenance, stage-result normalization, scale limitations,
   workspace isolation, PL-0179 evidence retention, and PL-0180 resource
   policy behavior.
9. Public tests are behavior-sensitive and cover success, missing/invalid
   prerequisites, stage failure, cancellation, repeated cancellation, partial
   output, retry/recovery, source-byte preservation, output identity and
   provenance, unsupported/collision export cases, and regression behavior.
10. The exact locked full suite exits `0`; no new skip/xfail hides a finding.
    Unavailable `cv2`, Windows symlink privilege, absent native engine, and
    other environment limitations are reported truthfully.
11. Ruff, format, targeted/relevant mypy, compileall, project/static checks,
    `git diff --check`, protected-file/scope, dependency/lock,
    privacy/secrets/signing, generated/binary, and remote-visibility checks
    pass truthfully. Unchanged repository-wide debt is disclosed.
12. Each child log and the master log contain full GitHub URLs, exact SHAs,
    commands/results, expected/failure conditions, limitations, scope and
    privacy reviews, and correct final handoff markers. The master log indexes
    all three children and ends exactly `AWAITING_MILESTONE_AUDIT`.
13. No child changes `TASKS.md`, writes a ChatGPT audit, starts M08 or later,
    adds a neural/model runtime, claims physical/native/owner acceptance, or
    publishes private/confidential/generated reconstruction data.

Closure requires a fresh independent ChatGPT audit for every child and then a
separate milestone audit. Builder validation is not acceptance.
