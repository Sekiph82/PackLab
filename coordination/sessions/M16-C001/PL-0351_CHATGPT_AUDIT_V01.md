# PL-0351 | ChatGPT Independent Audit V01

Date: 2026-10-15  
Repository: `Sekiph82/PackLab` (verified **private**), branch `main`  
Scope: **PL-0351 only**, separate Windows runner verifies the exact prior PL-0350 Installer, not a rebuild.

## VERDICT: AUDITED_PASS_ENGINEERING_PORTABILITY

**The PL-0351 clean-hosted-Windows Installer portability and installed-application smoke task is accepted.** The real GitHub-hosted Windows Server 2022 consumer downloaded the exact prebuilt unsigned PL-0350 warm Installer, checked source and binary identities, installed it into an isolated runner-temp directory, launched the **installed** PackLabStudio.exe under a restricted environment, passed Qt GUI/PDF, native CAD/STEP/DXF and Open3D checks, and uninstalled with no install-tree residue. No OCCT/OCP build, Installer rebuild, owner Desktop change, public release, or separate deployment is asserted. This engineering pass is **not** a factory rollout authorization, retail clean-PC certification, legal sign-off, or claim that the host had no prior VC++ runtime.

### Independently checked sources

- Successful separate workflow execution: https://github.com/Sekiph82/PackLab/actions/runs/38703546854 ; **one** job `116317266108`, all 10 workflow steps `success`, head revision `0d08f8e84140951c45d766b4b9a39b231536302a`, `workflow_dispatch` on `main`, executed 2026-10-15 08:08–08:09 UTC. The full hosted job log was independently read by ChatGPT.
- Implementation: https://github.com/Sekiph82/PackLab/blob/main/.github/workflows/pl0351-clean-windows-installer-smoke.yml
- Focused source-level workflow contract test: https://github.com/Sekiph82/PackLab/blob/main/tests/ci/test_pl0351_clean_windows_workflow.py
- Implementer append-only log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CODEX_LOG_V02.md
- Original acceptance requirements: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CHATGPT_AUDIT_CRITERIA_V01.md
- Updated implementation scope: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CODEX_PROMPT_V02.md
- Independently accepted PL-0350 predecessor: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_ALL_REMAINING_WORK_ONE_SHOT_CHATGPT_AUDIT_V02.md
- True warm Installer producer: https://github.com/Sekiph82/PackLab/actions/runs/38649528145
- GitHub private-repository metadata independently verified `private=true`, `visibility=private`; at audit start `main=b99e09aebc783573da1d4c1406feadd338711921` and latest log-only commit changed only PL-0351 log.

### Real acceptance evidence from the independent job

| Check | Evidence | Result |
| --- | --- | --- |
| Dedicated host and dispatch | Fresh GitHub-hosted `windows-2022` job `116317266108`, not producer, manual `workflow_dispatch`, 35-min maximum | **PASS** |
| Exact source artifact | PL-0350 warm run `38649528145`, artifact **11935390977**, archive **877,253,435** bytes and outer digest `3e9762e4d3faf6d0363f9714bfbdcb0d0b2d9dc9e73769ebfaac757c9af23e15` independently matches producer artifact API, produced source `452fe8934b0d56011af8c117555dd059d5c63462` | **PASS** |
| Exact unsigned setup EXE | Actual downloaded Installer **877,598,790** bytes and SHA-256 `3e7c13c18674fbe0a4de843a2ac329055850d07901a7e33fac8a3dc742d92da6`, unsigned, producer metadata and installed-smoke evidence cross-checked | **PASS** |
| Installed binary identity | Freshly installed PackLabStudio.exe SHA-256 `65e342ae0da4b3e061f504e0ad7c8399315e0393bb8705b890abd6c4d5164b7e` equals producer installed binary hash; no checkout/staging substitution | **PASS** |
| Sanitary environment | Minimal Windows system+isolated application `PATH`, cleared developer/Python/Qt variables, `QT_QPA_PLATFORM=offscreen` for headless smoke | **PASS for tested conditions** |
| Windows MSVC prerequisite | x64 VC++ runtime was **already present**, detected version **14.51.36247.0**, minimum **14.44.35211.0**; no automatic download or unauthorized installation | **PASS when prerequisite present; missing-prerequisite path NOT tested** |
| QtCore loader and UI | Installed QtCore/Qt6Core native files present; real QApplication and StudioMainWindow startup through executable smoke; earlier `procedure could not be found` regression not reproduced | **PASS** |
| Qt / vector PDF | Installed QtSvg/QtPdf/PDF render/export group `qt_vector_pdf` PASS | **PASS** |
| CAD/geometry | `ocp_cad`, `step_io`, `dxf_export`, `open3d_geometry` all PASS; Open3D version **0.20.0** | **PASS** |
| Packaged network mode | Every six product capability groups report `network=NONE` and product smoke `PASS` | **PASS to instrumented product contract; no packet-capture or firewall proof** |
| Source/license evidence | Installed notices and Open3D notices present; Qt relinking/source guide present; 12 recorded source entries present | **PASS presence/manifest gate; no legal opinion** |
| Uninstall | Inno uninstaller executed on CI runner-owned install tree, `installer_uninstall=PASS install_tree_residue=NONE` | **PASS** |
| CI publication | No new artifacts uploaded for this run, private repo, source implementation/test commit distinct from log-only commit | **PASS** |

The full job log has precise final gates:
`installed_app=PASS ... QtCore_loader=PASS_via_QApplication_StudioMainWindow ... corresponding_source_records=12 ... Open3D=0.20.0 network=NONE ... sanitized_PATH=Windows_system_directories_and_isolated_install_only`;
`installer_uninstall=PASS install_tree_residue=NONE`;
`PL0351_HOSTED_ACCEPTANCE=PASS`.
An earlier run `38703187808` also had a successful job; the independent verdict uses the later source-exact success `38703546854`, not any earlier failed retries.

### Source and regression audit

- Final workflow head commit `0d08f8e84140951c45d766b4b9a39b231536302a` changes **only** the PL0351 workflow and its contract tests. Log-only latest commit modifies **only** `PL-0351_CODEX_LOG_V02.md`. No project build/locked native input changed.
- Focused contract tests **2/2 PASS** per Codex log. Ruff lint/format, targeted mypy and Git diff checks reported PASS. No full repository quality rerun, explicitly appropriate here because this is isolated workflow/harness-only work; predecessor PL0350's **2158 PASSED** is historical, not relabeled as new PL0351 quality.
- Implementation checked exact Actions artifact origin/expiry, compiled Installer bytes/signature/metadata, installed executable producer provenance, QtCore/PDF/native capability manifests, no developer DLL injection, and isolated uninstall. Test source is structural (two workflow-text contract tests), not comprehensive negative tests; however, real installed-runner pass provides the decisive functional proof. Negative runtime failure paths were not injected dynamically in this acceptance run.
- **Minor nonblocking evidence-format defect:** final `PL0351_HOSTED_ACCEPTANCE` log line prints `capability_manifest_sha256` twice, with a duplicate empty trailing value due an unused output reference. The **real first** SHA-256 is populated and matches the `installed_app=PASS` line: `dae2f51d171e9475e22d43278eb94fe9d10ac17c31bc35cc84acc6b08d53ee57`. This does not void the earlier nonempty and computed app-manifest gate; correct this duplicate during normal future workflow maintenance **without repeating the native build**.
- No independent on-owner-laptop hashing of preserved source/exe, human visual GUI interaction, fresh retail Win11 device, missing VC++ prerequisite failure scenario, or clean Kenya factory machine test occurred. They MUST NOT be described as already passed.

### Security/deployment boundary

- Project remains **proprietary internal business** for user's controlled computers and future authorized Kenya factory PCs, NOT a public or personal-only license.
- `legal_review_required=true`; `public_release_authorized=false`. PL0350's engineering notice/source mapping was green, but formal legal review before inter-company distribution or factory rollout remains outside this technical smoke.
- Do not expose the private Installer, source, user scans, business assets or GitHub artifacts. No digital signature was applied. No owner device installation or destructive cleanup was part of PL0351.
- PL0351 test workflow is **bound to warm artifact 11935390977**, scheduled to expire **2026-10-15 23:08:28 UTC**. It will not remain re-runnable after expiry unchanged. Preserve the locally retained verified warm Installer and report, and redesign future smoke input to a durable owner-private provenance-verified store **in a separately authorized maintenance task**, rather than silently rebuilding OCCT/OCP or substituting a different Installer.

## Final auditor judgment

**PL-0351 = AUDITED_PASS_ENGINEERING_PORTABILITY.** The intended fresh hosted-Windows installed-app smoke passed independently, including the high-priority QtCore loader regression. This completes PL0351 engineering acceptance only. PL0352 can be planned after canonical tracker handoff; note that its historical wording `public repository` now conflicts with owner's private-repository decision and needs ChatGPT-owned adaptation. No automatic factory deployment, legal certification, installer signing, or unrelated M17 tasks are authorized.

**Tracker policy:** Codex must not edit root `TASKS.md`. ChatGPT should record PL0350 engineering PASS, PL0351 PASS and PL0352 as next scope, retaining a distinct formal legal/factory release gate. If an attempted canonical edit is rejected by platform safety, report that precisely rather than claim root tracker synchronization.
