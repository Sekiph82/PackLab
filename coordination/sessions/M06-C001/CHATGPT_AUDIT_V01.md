# M06-C001 — ChatGPT Independent Audit V01

Date: 2026-09-27
Scope audited: PL-0135 through PL-0149 as currently published on `main`
Remote head inspected: `0442a3fea64d5133f9ccdac788444fbe0407caf4`
Overall result: **CHANGES_REQUIRED**

This is a partial M06 audit. PL-0150 through PL-0157 are not implemented and are outside this audit. M06 remains open.

## Evidence reviewed

- Root task state:
  https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
- Master work order:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
- Master audit criteria:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md
- Published PL-0135..PL-0149 source, tests, prompts, criteria and available child logs on remote `main`.
- Current production Studio sources under:
  https://github.com/Sekiph82/PackLab/tree/main/apps/windows-studio/src/packlab_studio
- Current Studio tests under:
  https://github.com/Sekiph82/PackLab/tree/main/tests/studio

The latest builder-reported local suite is `262 passed, 4 skipped, 1 deselected`. That run is useful supporting evidence but was not independently re-executed by this audit. Audit decisions below are based on published source/test behavior and required artifact completeness.

## Publication boundary

Remote `main` contains PL-0149 implementation through:
https://github.com/Sekiph82/PackLab/commit/0442a3fea64d5133f9ccdac788444fbe0407caf4

The remote M06 session directory does **not** yet contain:
- `PL-0145_CODEX_LOG_V01.md`
- `PL-0149_CODEX_LOG_V01.md`
- `MASTER_CODEX_LOG_V01.md`

The builder reported these publication artifacts are committed locally but not pushed because GitHub DNS failed. They must be published before those artifact gates can close.

## Child results

| Task | Result | Audit note |
|---|---|---|
| PL-0135 | AUDITED_PASS | Single QApplication ownership, import-safe app entry point and offscreen shell tests are present. |
| PL-0136 | AUDITED_PASS | Five stable routes, central controller and accepted M05 Capture Inbox service composition are present. |
| PL-0137 | AUDITED_PASS | Stable dock IDs, one dock inventory and deterministic workspace reset are present. |
| PL-0138 | CHANGES_REQUIRED | Geometry sanitization is tested only when explicit screen bounds are passed to the helper. Production restore calls `PreferencesStore.load()` without screen bounds and then directly applies saved geometry, so a previously valid but now off-screen window can still restore off-screen. |
| PL-0139 | AUDITED_PASS | Central JobManager, bounded messages, deterministic logical ordering and presentation-only JobPanel composition are present. |
| PL-0140 | CHANGES_REQUIRED | Production uses the existing `packlab_core.subprocess_runner` through `OwnedSubprocessJob`, but the mandatory audit coverage does not exercise that production subprocess adapter or prove the no-unrelated-process boundary. Current shutdown tests exercise generic cancel hooks only. |
| PL-0141 | CHANGES_REQUIRED | Diagnostics are atomic/bounded/redacted, but the service is not integrated through the production shell/project seam and does not itself collect an active project summary. Mandatory production-seam coverage is missing. |
| PL-0142 | AUDITED_PASS | Local-only About/version reporting and malformed/unsupported/no-manifest states are implemented without online update/install behavior. |
| PL-0143 | AUDITED_PASS | Versioned project layout, safe relative paths, raw/working/derived/export separation and traversal rejection are present. |
| PL-0144 | CHANGES_REQUIRED | `ProjectManager` owns lifecycle, but the shell only stores it as navigation context. Required route/workspace availability is not actually bound to open/closed project state. Switching via `new_project()` can also create the new project on disk before an active-job close veto is evaluated. |
| PL-0145 | ARTIFACT_BLOCKED | Published implementation provides UUID/revision metadata and stale-revision checks, but the mandatory child log is absent from remote `main`; closure is blocked until the existing local log commit is published and verified. |
| PL-0146 | CHANGES_REQUIRED | Individual JSON writes are atomic, but authoritative editable state and its revision metadata are published as two separate replacements. A crash/failure between them can expose a new `state.json` with the old project revision, so the required transactional autosave boundary is incomplete. |
| PL-0147 | CHANGES_REQUIRED | Logical history is append-only and integrity chained, but persistence appends directly to the live JSONL file rather than atomically publishing a complete valid history state. Mandatory atomic-persistence/revision-continuity failure coverage is incomplete. |
| PL-0148 | CHANGES_REQUIRED | Recovery classification is implemented, but it is not wired into `ProjectManager`/shell lifecycle. `StudioMainWindow.recovery` remains `None`; clean/open/abnormal-close production integration required by the criteria is absent. |
| PL-0149 | CHANGES_REQUIRED | Provenance/invalidation exists and is atomically persisted, but mandatory stale-reopen coverage and a clear UI/job-planning query seam are incomplete. The mandatory child log is also absent from remote `main`. |

## Required remediation

1. Publish the already-created local-only PL-0145 log, PL-0149 log and master batch-stop log without reset, rebase, force-push or history rewriting.
2. Remediate PL-0138 production geometry restore against current screen bounds.
3. Add production-boundary PL-0140 subprocess cancellation tests proving PackLab-owned cancellation and no unrelated-process termination.
4. Integrate PL-0141 diagnostics through project/shell services and test the production seam.
5. Bind PL-0144 route/workspace availability to ProjectManager lifecycle and make project switching failure-safe before publishing a new project destination.
6. Make PL-0146 authoritative editable-state + revision publication transactionally crash-safe.
7. Make PL-0147 history persistence atomically publish a valid append-only logical history and strengthen revision continuity tests.
8. Integrate PL-0148 recovery into project/shell open/close lifecycle with production-seam tests.
9. Complete PL-0149 stale-reopen/query seam tests and publish its child log.
10. Re-run the exact locked suite and all required static/project checks.
11. Do not start PL-0150 until this remediation receives independent `AUDITED_PASS`.

## State

Accepted in this audit: **PL-0135, PL-0136, PL-0137, PL-0139, PL-0142, PL-0143**

Still open: **PL-0138, PL-0140, PL-0141, PL-0144, PL-0145, PL-0146, PL-0147, PL-0148, PL-0149**

M03–M05 acceptance remains undisturbed. PL-0068 remains OWNER_REQUIRED. M07 remains not started.

**CHANGES_REQUIRED**
