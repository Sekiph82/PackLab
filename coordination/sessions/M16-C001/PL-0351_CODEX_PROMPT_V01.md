# PL-0351 - Codex Prompt V01

Task: **Packaged Windows application clean-artifact portability smoke test**
Milestone: **M16 - CI/CD, Signing & Distribution**
Cycle: **M16-C001**

> Amended before first execution on 2026-10-06 after owner-machine evidence showed `ImportError: DLL load failed while importing QtCore: The specified procedure could not be found.` The exact failing local binary could not be tied to the hosted PL-0349 stage, so cross-job artifact/install portability is now a mandatory gate.

## M16 global rules

- Read live root TASKS.md, M15 final audit, M14 final audit, the dependency/license register, versioning policy, secrets policy, exact predecessor prompt/criteria, PL-0349 V03 audit, and PL-0350 final accepted evidence before implementation.
- Root TASKS.md lifecycle is ChatGPT-owned; Codex must not edit it.
- M16 owns CI/build/release engineering only. Do not alter domain authority or pull M17 work forward.
- GitHub Actions permissions remain least-privilege. No signing secrets are needed.
- No private/proprietary scan, supplier attachment, POVU production artwork, certificate, key, token, checkpoint or owner-local path may enter public CI artifacts.
- Runtime/build provenance must remain path-private.
- No hidden runtime network/download behavior may be added.
- PL-0368 remains post-M17 deferred.

## Preconditions

Do not start until PL-0350 is builder-green and has produced an exact cleared unsigned installer artifact whose provenance binds:

- Studio semantic version;
- PackLab build revision;
- installer SHA-256 and byte length;
- exact cleared staging/compliance evidence.

The smoke must test that exact artifact, not a locally rebuilt substitute.

## Required CI architecture

Add a **separate fresh Windows job** whose only application-under-test input is the uploaded PL-0350 installer artifact from the upstream build job.

The portability job must:

1. run on a fresh `windows-latest` runner/job;
2. not use the producer job's staging directory;
3. download the exact installer artifact via a full-SHA-pinned reviewed `actions/download-artifact`;
4. validate downloaded installer SHA-256/length against PL-0350 provenance before execution;
5. install silently into an isolated CI path;
6. launch the **installed** `PackLabStudio.exe`, never the producer-job staging EXE;
7. uninstall/cleanup even on failure.

A source checkout may exist only for workflow/test harness logic. The installed application must not import PackLab/PySide/OCP/Open3D from the checkout or a CI virtual environment.

## Sanitized runtime environment

The smoke exists specifically to catch environment-dependent DLL success.

Before launching the installed application:

- do not prepend repository `.venv`, Python site-packages, Qt, Shiboken, Open3D, OCP, Poppler, Conda or unrelated developer tool directories to `PATH`;
- use a minimal/system-oriented PATH sufficient for Windows and the installed program;
- clear Python-specific variables that could leak source/runtime dependencies, including `PYTHONPATH`, `PYTHONHOME`, and equivalent PackLab development overrides;
- do not set `QT_PLUGIN_PATH`, `QML2_IMPORT_PATH`, `PYSIDE_DESIGNER_PLUGINS`, or external Qt DLL search paths;
- set only the explicit offscreen flag required by the smoke when necessary.

Record a path-private statement that no checkout/venv Qt/Python DLL directory was available to the process.

## Mandatory installed-app smoke

Run the installed executable through its existing noninteractive build-smoke seam and require nonzero failure propagation.

It must prove from the installed artifact:

### Startup and provenance
- process starts and exits cleanly;
- embedded build revision/Studio version match installer provenance;
- installed executable and required provenance files exist only under the install tree.

### Qt loader portability
- `PySide6.QtCore` loads successfully;
- QApplication/offscreen startup succeeds;
- StudioMainWindow construct/show/process/close succeeds;
- no `DLL load failed`, `specified procedure could not be found`, missing-entry-point, plugin-load, ICU mismatch or Shiboken loader error occurs.

### Technical PDF
- real QtSvg + QtPdf capability succeeds;
- bounded PackLab vector PDF export + QPdfDocument parse/render smoke passes.

### CAD/geometry
- OCP/CAD probe and bounded PackLab CAD operation pass;
- Open3D 0.20.0 probe and bounded PackLab geometry operation pass.

### Network
- smoke requires no runtime network/download.

## Native dependency diagnostic on failure

If startup fails with a Windows native loader error, do not merely retry.

Capture path-private diagnostic evidence sufficient to classify:

- missing DLL;
- wrong DLL/version loaded;
- missing procedure/entry point;
- architecture mismatch;
- Qt/Shiboken version mismatch;
- foreign ICU/Qt/OpenSSL/runtime DLL interference.

Use safe local tooling available on the runner, PowerShell/PE metadata, or a reviewed pinned diagnostic utility if genuinely necessary. Do not dump user paths/secrets.

The job must remain failed until root cause is fixed. Do not catch/ignore the loader failure.

## Optional installer behavior

If PL-0350 defines an external Microsoft Visual C++ runtime prerequisite:

- validate the installer prerequisite behavior truthfully;
- do not auto-download the prerequisite;
- if the hosted runner already satisfies it, record detected version;
- do not bundle an unapproved runtime solely to make the smoke pass.

## Required evidence

Publish or preserve in job logs/artifact metadata:

- downloaded artifact name/ID;
- installer SHA-256/length;
- source build revision/version;
- install path represented only by logical placeholder/category, not owner-specific canonical identity;
- installed executable SHA-256;
- smoke capability statuses;
- sanitized-environment contract result;
- uninstall/cleanup result.

Do not upload the installed application tree as new evidence unless separately authorized.

## Local/static validation

Run relevant workflow contract tests, Ruff/format/mypy/compile for changed Python/tools, locked full pytest, secrets/privacy/scope checks, and `git diff --check`.

## Stop rule

Stop and publish a blocker if:

- the exact installer cannot be downloaded/verified;
- installed app depends on checkout/venv paths;
- QtCore or another required native module fails to load;
- installed PDF/OCP/Open3D capability fails;
- prerequisite behavior is ambiguous;
- cleanup cannot be made safe;
- a new unreviewed runtime dependency is required.

Do not continue to PL-0352 on such failure.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M16-C001/PL-0351_CODEX_LOG_V01.md` in a distinct log-only commit.

Record exact hosted run/job/artifact IDs, installer hash, sanitized-environment result, installed capability results, cleanup, validation and final parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
