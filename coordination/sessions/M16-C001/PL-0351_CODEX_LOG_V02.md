# PL-0351 Codex Log V02 — Clean Windows Installer Portability

Date: 2026-10-15
Repository: private `Sekiph82/PackLab`, canonical branch `main`
Task: PL-0351 only

## Disposition

**Hosted fresh-Windows installed-app acceptance PASS.** The exact retained PL-0350 warm unsigned Installer was downloaded by artifact ID, provenance-checked, installed on a separate GitHub-hosted Windows 2022 runner, exercised from its isolated install tree with the sanitized runtime contract, and uninstalled successfully. This is implementer evidence for independent audit. It does not grant formal legal clearance or authorize Kenya factory deployment.

## Authority, synchronization, and input identity

- Read the full `PL-0351_CODEX_PROMPT_V02.md`, matching linked `PL-0351_CHATGPT_AUDIT_CRITERIA_V01.md`, prior V01 prompt, PL-0350 one-shot report, and independent PL-0350 audit V02 before implementation.
- PL-0350 V02 independently states `AUDITED_PASS_ENGINEERING_INSTALLER_AND_WARM_CACHE` and explains that the PL-0350 `TASKS.md` line is stale because the lifecycle write was blocked. The V02 prompt expressly authorizes proceeding on that independent engineering acceptance. Root `TASKS.md` was not modified.
- Initial local HEAD `30efa68010830a4a08743e3adf4b7829b3e4657c`, clean; fetched `origin/main` at `ad7f795fadbc2b8590da31597b33ca8ab4483b88`; fast-forwarded without reset/stash. Three commits were then ahead of main during publication; all pushes were fast-forward only.
- Final implementation revision tested by the successful hosted run: `0d08f8e84140951c45d766b4b9a39b231536302a`.
- Exact application under test: PL-0350 warm artifact `11935390977`, producer run `38649528145`, source revision `452fe8934b0d56011af8c117555dd059d5c63462`, artifact name `packlab-windows-installer-452fe8934b0d56011af8c117555dd059d5c63462`.
- At run time the private artifact API reported 877,253,435 archive bytes, digest `sha256:3e9762e4d3faf6d0363f9714bfbdcb0d0b2d9dc9e73769ebfaac757c9af23e15`, and expiry `2026-10-15T23:08:28Z`. Run `38703546854` started at `2026-10-15T08:08:23Z`, before expiry.
- Downloaded unsigned Installer: 877,598,790 bytes, SHA-256 `3e7c13c18674fbe0a4de843a2ac329055850d07901a7e33fac8a3dc742d92da6`; metadata and producer installed-smoke evidence matched the source revision and Installer digest. Authenticode status was `NotSigned`.

## Implementation

- Added `.github/workflows/pl0351-clean-windows-installer-smoke.yml`: manual dispatch on `main` only, separate `windows-2022` job, 35-minute bound, least-privilege `actions:read` and `contents:read`, full-SHA-pinned checkout/download actions, exact producer run/artifact IDs and locked hashes. It does not invoke the PL-0350 build workflow or any OCCT/OCP/PyInstaller/Installer build.
- The consumer validates artifact API name, ID, size, digest, expiry and producer run/source SHA before download; then validates exactly one expected Installer, its SHA/length/signing state, metadata, and producer installed executable identity.
- The job checks the x64 Microsoft VC++ prerequisite from the runner registry and requires version 14.44.35211.0 or later. Observed hosted version: **14.51.36247.0**. No runtime was downloaded or installed by the workflow.
- Installer destination is a fresh unique CI runner-temp directory. The smoke process runs from the installed executable with `PATH` limited to Windows system directories and that isolated application tree. Python, Qt plugin, QML, Shiboken Designer, and all ambient `PACKLAB_*` variables are cleared; only the expected build revision/version and smoke output locations are restored. `QT_QPA_PLATFORM=offscreen` is used for this headless runner.
- Before execution the workflow verifies exactly one installed `QtCore.pyd` and `Qt6Core.dll`, installed third-party notices, Open3D third-party license corpus, Qt relinking guide, source-delivery manifest identity, and the presence of all 12 manifest-listed corresponding-source records.
- The installed application's existing `--packlab-build-smoke` seam requires successful QApplication/StudioMainWindow startup and close, technical drawing PDF export plus QtPdf parse/render, OCP CAD/revolve/bounds/tessellation, STEP round trip, DXF output, and Open3D/NumPy geometry. Every reported capability group is required to pass with `network=NONE`; Open3D must report 0.20.0. The application emitted a PASS manifest from the installed app.
- An unconditional cleanup step invokes the Inno uninstaller and verifies the isolated install tree is removed. It checks its target stays under runner temp and rejects a reparse point. No owner-host installation is changed.
- Workflow writes only path-redacted text to the Actions log/summary. It uploads no Installer, installed app, product sample, private source archive, owner path, secret, or signing material.

## Hosted result

Final evidence: [GitHub Actions run 38703546854](https://github.com/Sekiph82/PackLab/actions/runs/38703546854), job `116317266108`, head `0d08f8e84140951c45d766b4b9a39b231536302a`, conclusion **success**, elapsed 1m25s.

The directly inspectable job log records:

- Artifact/run/source identity and matching archive digest/size; exact Installer SHA-256/byte length and `signing=unsigned`.
- Microsoft x64 runtime version 14.51.36247.0; automatic prerequisite download disabled.
- Installed executable SHA-256 `65e342ae0da4b3e061f504e0ad7c8399315e0393bb8705b890abd6c4d5164b7e`.
- Runtime capability manifest SHA-256 `dae2f51d171e9475e22d43278eb94fe9d10ac17c31bc35cc84acc6b08d53ee57`.
- `QtCore_loader=PASS_via_QApplication_StudioMainWindow`; QtPdf PASS; notices present; all 12 corresponding-source records present; Qt GUI/PDF, OCP CAD, STEP, DXF, and Open3D 0.20.0 groups PASS; `network=NONE`; sanitized path contract PASS.
- `installer_uninstall=PASS install_tree_residue=NONE`; final gate `PL0351_HOSTED_ACCEPTANCE=PASS`.

## Validation and run history

Local checks against the workflow contract:

- `uv run --locked --no-sync pytest tests/ci/test_pl0351_clean_windows_workflow.py -q` — **2 passed**.
- `uv run --locked --no-sync ruff check tests/ci/test_pl0351_clean_windows_workflow.py` — PASS.
- `uv run --locked --no-sync ruff format --check tests/ci/test_pl0351_clean_windows_workflow.py` — PASS.
- `uv run --locked --no-sync mypy tests/ci/test_pl0351_clean_windows_workflow.py` — PASS.
- `git diff --check` and `git diff --cached --check` — PASS.
- GitHub recognized the committed workflow, and run `38703546854` executed all workflow steps successfully. A local standalone YAML parser/actionlint was unavailable; hosted workflow parsing and execution provide the syntax/runtime validation.
- The first three hosted attempts (`38702317412`, `38702530732`, `38702804938`) exposed two harness-only mistakes: the environment scrub initially removed expected test labels, then a post-smoke check referenced a scrubbed value. The first two stopped before successful capability execution; the third's installed app smoke itself passed but the workflow's manifest identity gate failed. All three runs executed the isolated uninstall successfully. Both were corrected in the workflow; the subsequent complete runs `38703187808` and `38703546854` passed every job step. No PackLab application binary change or Installer rebuild was needed.
- Full repository Quality was not rerun: only a manual consumer workflow and its static contract test changed; PackLab application sources, packaging sources, lockfiles, and Installer were untouched. PL-0350 Quality is referenced only as predecessor evidence, not relabeled as a PL-0351 test.
- No OCCT/OCP compilation, Installer rebuild, disk cleanup, file deletion, Desktop/working PackLab modification, owner binary access, or `TASKS.md` edit occurred. Repository API still confirms `private=true`, `visibility=private`, default branch `main`.

## Scope, privacy, and limitations

- Changed files: new PL-0351 workflow, its focused contract test, and this log. No future PL-0352/M17/PL-0368 work was started.
- The hosted runner is a fresh GitHub Windows 2022 job, not an untouched retail PC. Its installed VC++ prerequisite was observed and recorded.
- `network=NONE` is the product smoke's declared capability contract; this run did not apply a host firewall or packet-capture policy. The installer and app test performed no runtime download step.
- Evidence verifies installed source/notice presence and source-manifest identities, not a legal opinion. Formal legal review remains pending and factory deployment is not authorized by this engineering test.
- This test does not independently inspect the owner's Desktop, perform manual visual acceptance, or certify install/upgrade behavior on a separate physical workstation.
- No public Release or tag was created. No legal clearance or external redistribution permission is claimed.

## Publication

- Implementation commits, pushed fast-forward to private `main` in order:
  - `5a66534a286ded311d9e25924c942131c66bf6ff` — add consumer workflow and contract tests.
  - `1a23fcd68f24f9a1c86d52b829182cadc3d4de51` — path-redacted smoke diagnostics.
  - `3fb6dd42685a352239374b30fa47eddd032c1173` — preserve authorized smoke identity through environment scrub.
  - `18a5e1df51397a6c62b7b506c6d34c655961a2d9` — compare manifest with saved expected identity.
  - `0d08f8e84140951c45d766b4b9a39b231536302a` — expose acceptance evidence in hosted logs.
- The final PL-0351 log is published separately in a log-only commit after implementation and hosted verification.
- Final parity/private-state verification: run head matches the implementation revision; `origin/main` is synchronized; working tree was clean before writing this log; no `TASKS.md` edit.

READY_FOR_INDEPENDENT_AUDIT
