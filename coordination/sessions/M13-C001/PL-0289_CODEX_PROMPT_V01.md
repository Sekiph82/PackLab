# PL-0289 - Codex Work Order V01

Task: **Benchmark/select supported Python OpenCascade binding for Windows packaging**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0289_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0289_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 batch / READY / CODEX. Re-read the M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical-validation deferral, repository rules and this child criteria. Fetch and fast-forward only if clean and behind-only. Preserve owner-local work; never reset, clean, rebase or force-push.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/pyproject.toml
- https://github.com/Sekiph82/PackLab/blob/main/uv.lock
- https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/DEPENDENCY_LICENSE_REGISTER.md
- https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0005-standalone-design-geometry-root.md

## Frozen scope

Evaluate current Python OpenCascade binding candidates against PackLab's actual Windows x86-64 / CPython 3.12 / uv environment. Candidate review must include at least the realistic pip/uv path and pythonocc-core as a comparison where feasible, but no package is preselected. Selection criteria: installability in the locked PackLab environment, successful import, exact OCCT/kernel version visibility, STEP/BREP/tessellation/boolean capability probes needed by M13, wheel/native artifact provenance, license of the binding itself, OCCT license/exception, transitive native contents, package size/redistribution attention, and compatibility with a PackLab-owned adapter. Pin exactly one supported binding only if the evidence is sufficient. If none passes, stop BLOCKED rather than inventing compatibility. No runtime auto-download or vendor binary fetch.

## CAD authority and physical-validation rules

- CAD/BREP is a derived engineering representation of exact Design Model revision truth.
- CAD never replaces Scan Master or Design Model authority.
- CAPTURED_SCAN_MASTER and STANDALONE_DESIGN_GEOMETRY parent modes remain explicit.
- `METRIC_UNVERIFIED` / `mm_unverified` remains unverified; `RELATIVE` must never silently become mm.
- Topology validity, STEP/STL validity or successful export is not evidence of physical accuracy, mold readiness or manufacturing suitability.
- PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: candidate matrix; exact selected package/version/build; Windows CPython 3.12 install/import; kernel/version probe; BREP/revolve/loft/boolean/tessellation/STEP capability smoke; wheel/native digest evidence; binding license separate from OCCT license; lockfile update; no runtime download; unavailable candidate reasons.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, dependency/license/privacy/secrets/generated/binary/scope/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green and no real stop condition exists, continue directly to PL-0290 under the master batch without waiting for intermediate ChatGPT audit. Stop only on FAILED/BLOCKED/OWNER_REQUIRED/master stop.
