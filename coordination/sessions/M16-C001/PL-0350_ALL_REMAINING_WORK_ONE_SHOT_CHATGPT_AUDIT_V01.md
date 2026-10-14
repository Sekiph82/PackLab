# PL-0350 ONE-SHOT | Independent ChatGPT Audit V01

Date: 2026-10-14
**Verdict: AUDITED_PARTIAL_CHANGES_REQUIRED / BLOCKED_OWNER_AND_REDISTRIBUTION_EVIDENCE**
**PL-0350 REMAINS OPEN. No Windows Installer artifact or cold-to-warm full production acceptance.**
This is a single consolidated end-to-end audit under the owner's ONE-SHOT PL-0350 work arrangement. No new numbered remediation task or R07/R08 mini-prompt is authorized by this audit.

## Independently verified sources

- Builder ONE-SHOT report: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_ALL_REMAINING_WORK_ONE_SHOT_REPORT.md
- Builder append-only log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_ALL_REMAINING_WORK_ONE_SHOT_CODEX_LOG.md
- Source SHA `bb50690b8e932cbd8bb9f04504f36ed798698faa`.
- Evidence commit `10261dca`: https://github.com/Sekiph82/PackLab/commit/10261dca
- True cold/packaging run: https://github.com/Sekiph82/PackLab/actions/runs/38617631153
- GitHub Windows Python quality PASS: https://github.com/Sekiph82/PackLab/actions/runs/38617544058
- Source owner authority and original ONE-SHOT task: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_ALL_REMAINING_WORK_ONE_SHOT_MASTER_CODEX_PROMPT.md
- Exact original audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_ALL_REMAINING_WORK_ONE_SHOT_CHATGPT_AUDIT_CRITERIA.md
- Official Qt LGPL obligations: https://www.qt.io/development/open-source-lgpl-obligations
- Actual PySide6 6.11.2 distribution/license: https://pypi.org/project/PySide6/6.11.2/
- Open3D pinned v0.20.0 MIT source and component inventory: https://github.com/isl-org/Open3D/blob/v0.20.0/LICENSE and https://github.com/isl-org/Open3D/blob/v0.20.0/3rdparty/README.md
- Microsoft runtime file redistribution policy: https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files and https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute

Auditor independently fetched live evidence files, GitHub Actions latest-attempt **job table**, complete package-job log, and Actions artifact metadata (IDs/sizes/SHA/expiry), and examined primary Qt/Open3D license-source guidance. The local Desktop git/files and host-executed tests were not rerun by ChatGPT. This is a technical/software evidence audit, **not a legal opinion or commercial Qt license acquisition**.

## A. Verified implementation progress

1. **PASS, independent GitHub evidence:** `Measure hosted storage and build inputs`, `Restore and preflight retained PL-0350 R04 OCCT SDK`, `Build and seal locked OCCT SDK checkpoint`, and `Build and seal official 315-module no-VTK OCP runtime` jobs were green in run 38617631153. Native CAD runtime was validated; the builder log confirms authenticated SDK and quarantined OCP reused without re-running OCCT/OCP native C++ compilation this time.
2. **PASS, independent hosted evidence:** `Package and smoke-test production Studio` successfully produced staging and advanced through frozen NumPy 2.5.3, isolated Open3D 0.20.0, exact frozen Qt module checks, OCP CAD, STEP/DXF, and all six offline Studio capability smoke groups **before** compliance. This resolves the prior Open3D/NumPy frozen-loader blocker.
3. **PASS, independent GitHub evidence:** 38617544058 locked Quality `success`, reporting according to builder `2,149 passed, 10 skipped, 1 deselected`, Ruff/format/mypy. No test result is substitute for distribution clearance.
4. **PASS, correct fail-closed stop:** Host log records `Compliance status: BLOCKED; staged files: 479; unresolved items: 9`. `Enforce redistribution clearance` is the ONLY failing action in package job. Its installer/clearance downstream steps were skipped, not successful. No actual unsigned Installer and no production full cold+warm proof exist.
5. **Builder-reported owner safety:** final managed worktree clean at `origin/main`; Desktop checkout unchanged, **3** local changes (1 tracked + 2 untracked) rather than historical claim of 10, initial/final hashes in builder log. No independent access to Desktop, so auditor does not elevate this to direct verification.

## B. Real hosted artifacts and expiry

Actions API for run 38617631153 independently returned:
- Source-built OCCT SDK: artifact **11921297195**, 57,520,243 bytes, archive sha256 `a14f2660e3627b4ee88f7a7f1d6b4c66f9cdb2e6a9022990d64ba5d616a2ee72`; expires **2026-10-15 19:03:30 UTC**.
- Sealed controlled OCP runtime: artifact **11922382361**, 46,462,994 bytes, sha256 `1a62424b85845eecd61be8a9706fb367258faaf8ae0dab63b2cbb7cfe1774e0b`; expires **2026-10-15 19:09:52 UTC**.
- Source evidence: artifact **11921068651**, 1,466 bytes, sha256 `3179d44b102a53960ba2f881d1330d3a5add61f6c0c7ec03931012598b4d88f4`; expires **2026-10-15 19:03:38 UTC**.
- Staged compliance pre-clearance: artifact **11922367788**, 305,713 bytes, sha256 `fd46a7e14299845b9f65055451b6549bc90de6c41ed2c3d43aa1a6d8fbf0ee02`; expires **2026-10-15 19:12:44 UTC**.
- Smoke diagnostic artifact **11922542537**, 3,625 bytes, sha256 `d1d1070fce37c108864c438284f8c4d150b41d3bd0b486ad141e454d03f1eb2e`; expires **2026-10-28 19:12:30 UTC**.
- Earlier verified OCCT recovery artifact **11796717315**, longer expiry **2026-10-27 07:59:40 UTC**, remains a separate prior checkpoint.

**URGENT:** Preserve verified same-run OCP/runtime + compliance text evidence through a cheap noncompiling/manual retention or committed redacted immutable compliance report before Oct 15 expiry if future audit/remediation needs them. Do not repeat 2h native build or forge SDK origin/cache HIT to extend an artifact. Archive hashes are OUTER GitHub artifact identities, not substitutes for manifest-per-file verification.

## C. Exact unresolved compliance facts

Builder preclearance summary: **479 staged files, 514,901,343 bytes; 123 collected notices; 61 required notices; 2 missing notices; 1 missing source package; 28 unresolved shipped files; 6 unresolved components; 9 unresolved top-level items.** Status `engineering_packaging_status=BLOCKED`, `legal_review_required=true`, `public_release_authorized=false`. No forbidden Qt components reported. Nine top-level entries:
1. `component:microsoft-vc-runtime`
2. `component:open3d`
3. `component:packlab`
4. `component:pyside6-addons`
5. `component:pyside6-essentials`
6. `component:shiboken6`
7. `evidence:missing-notices`
8. `evidence:missing-source-packages`
9. `_internal/numpy.libs/msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll`

These are NOT necessarily nine independent requests for owner signatures. Technical evidence for the official Open3D wheel and its 3rd-party components, Qt/PySide6/Shiboken license/module/NOTICE/source obligations and actual NumPy hashed DLL byte/license/REDIST map must be gathered from the exact shipped wheels and authoritative upstream sources by **Codex under the existing ONE-SHOT scope**, rather than asking the owner to discover package notices.

**Actual owner-only decision:** PackLab's own code/assets redistribution rights and intended recipient scope (internal personal-use test vs third-party distribution/public release). License route for Qt/PySide6 must be established: the Qt LGPL v3 open-source path may permit proprietary PackLab code only **if** the actual shipped modules qualify and all mandatory library-source, notices, replacement/relinking rights and other LGPL obligations are satisfied. Qt commercial license is an alternative only with the owner's actual documented entitlement; do not assume a purchase or require one automatically. Official Open3D core v0.20.0 is MIT, but exact built/wheel third-party transitive license obligations still need itemized evidence.

**Microsoft hash-renamed DLL:** A Nu​​mPy `numpy.libs/msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll` in frozen package is an actual **SHIPPED** native file. Need its exact bytes, authenticode/publisher, original filename/version, matching official REDIST manifest and lawful distribution route; an official VC prerequisite claim does not automatically authorize redistributing this *additional renamed local copy*. Alternative packaging path may omit it only if actual NumPy/Open3D frozen smoke and signed-prerequisite compatibility survive. Do not unconditionally waive or strip DLL.

**Legal and technical distinction:** User intent to create internal unsigned Installer does **not** by itself prove PackLab's own ownership or third-party redistribution entitlement; nor does building a frozen app automatically amount to public release. Preserve an engineering vs public release boundary in reports.

## D. ONE consolidated remaining action, not nine new prompts

**Do NOT start a fresh R07/R08 or split into mini-prompts.** The existing ONE-SHOT contract governs **one comprehensive final compliance/installer closure pass**:

- First copy/preserve necessary runtime and text-only compliance evidence by short GitHub-hosted no-compile workflow or append-only checksummed repository evidence before the 1-day artifacts expire; zero source recompilation.
- Codex autonomously inventory 28 unresolved shipped files: group by precise owner and decide each source/license/notice requirement from exact locked wheel metadata + pinned official sources; classify *genuine owner-only* decisions separately. For 2 missing notices + 1 missing source archive, collect source-backed bytes/hash and pin evidence where redistributable. For Qt community LGPL route, produce valid source/notice/relinking compliance package and don't include GPL-only modules; for Open3D use MIT core plus exact 3rd-party wheel SBOM and notices; for Microsoft verify/replace/hash-reconcile each actually shipped DLL without inventing rights.
- Solicit at most ONE consolidated answer from owner for their own PackLab rightsholder/usage decision, and if necessary one documented license-selection choice, not nine separate approvals. Any unresolved legal issue remains BLOCKED, without claiming automatic legal sign-off.
- Rerun only bounded hosted stage/redistribution after evidence is in the repo, with exact verified **SDK/OCP cache reuse**. If engineering legally sufficient and zero unresolved, produce actual unsigned Inno Installer, upload SHA/size/manifest and exercise true warm-cache proof only after cold successful Installer.
- If legal entitlement cannot be established, keep no Installer/public release claim; publish precise final state and ask ONLY the remaining material owner decision, not generic new prompt.

## Independent disposition

**AUDITED_PARTIAL_CHANGES_REQUIRED / BLOCKED_OWNER_AND_REDISTRIBUTION_EVIDENCE.**
Technical packaging and Open3D smoke accepted; PL-0350 **NOT COMPLETE**. `TASKS.md` must reflect this independently audited frontier. All unfinished legitimate W07 compliance/Installer/W08 warm-cache work remains in ONE master, with no artificially generated new milestone or prompt cycle. PL-0351 clean-Windows portability test, M17, and PL-0368 not started.
