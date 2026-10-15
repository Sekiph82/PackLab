# PL-0350 | Independent ChatGPT One-Shot Audit V02

Date: 2026-10-15
Canonical repository: private `Sekiph82/PackLab`, branch `main`.
Owner scope: proprietary **internal business** software, current owner computer and upcoming multiple authorized Kenya factory workstations; **no customer sales and no public source/binary release**.

## Final disposition

**AUDITED_PASS_ENGINEERING_INSTALLER_AND_WARM_CACHE / FORMAL_LEGAL_REVIEW_REQUIRED / PUBLIC_RELEASE_NOT_AUTHORIZED.**

The scope of PL-0350's **engineering** deliverable has passed the independently verifiable hosted checks: a source-locked, actual **unsigned Windows Installer**, a complete **installed** no-network Studio capability smoke on hosted Windows, an independent **warm OCP cache HIT** with OCP native compilation visibly skipped, and zero unresolved **engineering redistribution inventory** findings. The project can move to the separately controlled PL-0351 clean-target acceptance planning/test. **This is NOT legal approval, external redistribution permission or field deployment sign-off.** Formal legal review is still required before distribution or deployment to any separate business entity, and factory release is not authorized here. Legal review remains tracked as a **separate explicit release gate**; the engineering task itself need not be held artificially open for a lawyer's decision.

Independent verification scope: GitHub connector read current private repository metadata, canonical current `main`, source/builder/evidence commits, V01 criteria, full last builder report, append-only log, first and second Windows hosted build job statuses/steps and logs, artifact ID/size/digest metadata, exact-SHA quality job logs, and the 2026-10-15 disk-cleanup report. No direct download/byte-for-byte unpack of the ~877 MB Installer; individual Installer file SHA is supported by installed smoke metadata and CI hash report, while the outer Actions archive digests were independently compared via API. Auditor did NOT inspect the owner's Desktop directly, operate the GUI manually, or perform a fresh clean-PC install, which belongs to PL-0351.

## Independent engineering checks

| Gate | Independent evidence | Result |
| --- | --- | --- |
| Canonical revision | `main=30efa68010830a4a08743e3adf4b7829b3e4657c`; final compiled source `452fe8934b0d56011af8c117555dd059d5c63462` | PASS |
| Private repository | Live repo API: `private=true`, `visibility=private`, default branch `main` | PASS; prior public exposure cannot be retroactively undone |
| Exact-SHA quality | https://github.com/Sekiph82/PackLab/actions/runs/38646355410; job log states `2158 passed, 10 skipped, 1 deselected, 2 warnings`; Ruff/format/mypy pass | PASS |
| Cold Installer | https://github.com/Sekiph82/PackLab/actions/runs/38646432056; all 5 jobs successful; real Inno installer compiled, installed, and six no-network capability groups tested | PASS |
| Second warm Installer | https://github.com/Sekiph82/PackLab/actions/runs/38649528145; all 5 jobs successful, installer built, installed and full smoke passed again | PASS |
| Native SDK & OCP | Both installer runs restored authenticated R04 OCCT SDK. OCP job `Restore exact official ... runtime cache` PASS; `Fail-closed validate restored OCP runtime cache` PASS; `Install ... native CAD smoke` PASS; OCP source-build and cache-save steps SKIPPED. Warm logs explicitly `Cache hit for` exact controlled 315-module key, `CONTROLLED_OCP_BUNDLE_VALID files=49`, `CONTROLLED_OCP_INSTALL_PASS`, `CONTROLLED_OCP_SMOKE_PASS ... CAD=valid-box STEP=round-trip`. | PASS, **true OCP cache hit**; no new OCCT/OCP compile |
| Frozen/installed capability | `Smoke-test packaged Studio without network` and `Install unsigned package and run installed capability smoke` are successful in BOTH runs. Installer job checks installed executable hash equality against staged executable, installed smoke manifest sha, six PASS groups with `network=NONE`: Qt GUI, Qt PDF/vector, OCCT/OCP CAD/revolve/tessellation, STEP I/O, DXF, Open3D/NumPy. | PASS, hosted Windows only |
| File-level engineering inventory | Warm package job log explicitly `Compliance status: CLEARED_FOR_PL0350_ENGINEERING_PACKAGING; staged files: 622; unresolved items: 0`. Full report records 622/622 mapped files, 1,283,197,252 staged bytes, 126 notices collected/63 required, zero missing notices/sources/components/files, zero forbidden Qt. Compliance gate/final revalidation/source delivery and real installer build all executed and passed, NOT bypassed. | PASS for automated engineering inventory; NOT formal legal approval |
| Owner Desktop protection | Builder says original 3 owner changes preserved by matching SHA; audit does not have direct local Desktop access. | Builder-reported; not independently proven |
| Non-public release | No public installer/tag/release claimed; repository visibility independently confirms private; legal flags `legal_review_required=true` and `public_release_authorized=false`. | PASS for controlled engineering process |

A failed earlier warm dispatch `38649365194` did **not** qualify, because its downstream jobs were skipped. The subsequent `38649528145` is the proper warm proof.

### Binary and evidence identity

- Produced executable, unsigned Installer (`PackLabStudio-0.1.0-452fe8934b0d56011af8c117555dd059d5c63462-unsigned-setup.exe`): **877,587,276 bytes**, SHA-256 `8cc6fb20e4b88093a8647a5c5c511ee49db0a33de3c6d2c937c14b6544eb30f2` in reported build+installed smoke evidence.
- Cold Actions artifact **11933254991**, ZIP bytes **877,242,879**, ZIP SHA-256 `10e6a3564e35b9aa5c8a3946d145d8e9ebe61608149978dd7c787fe4ec1dd1c8`, expires **2026-10-15 22:40:14 UTC**.
- Warm Actions artifact **11935390977**, ZIP bytes **877,253,435**, ZIP SHA-256 `3e9762e4d3faf6d0363f9714bfbdcb0d0b2d9dc9e73769ebfaac757c9af23e15`, expires **2026-10-15 23:08:28 UTC**.
- Warm compliance final **11934773569**, bytes **345,753**, ZIP SHA-256 `29a1dc6014de36ec0c2b7db463bc28b7e4a8d6569e915d64b9069834c8260631`; expires **2026-10-15 23:04:28 UTC**.
- Warm preclearance **11934344670**, bytes **339,063**, ZIP SHA-256 `df84c88cc71549aba516cac4701ae81f102620cd1efbee73cf8232d81c1c08c6`; expires **2026-10-15 23:04:15 UTC**.
- Warm controlled OCP runtime **11934533271**, bytes **46,462,999**, ZIP SHA-256 `20b32a07237621820fff0610cf927a4f62a603525a900d9ce41690ff4197777d`; expires **2026-10-15 23:00:24 UTC**.
- Warm retained local Installer independently reported by builder as **877,598,790 bytes**, SHA-256 `3e7c13c18674fbe0a4de843a2ac329055850d07901a7e33fac8a3dc742d92da6`, preserved outside Desktop checkout. Cold Installer locally removed only after warm PASS; **do not confuse the different legitimate cold/warm executable hashes**. Source SHA is identical but output bytes may differ; each passed its own installed smoke. Auditor did not directly hash the local warm copy.

**Priority preservation:** The hosted binary/compliance and controlled runtime evidence above expires in <1 day at audit time. The locally retained warm installer MUST remain untouched and hash-checked before PL-0351, and the exact source/notices and associated audit evidence must stay available in private GitHub. No rebuild should be triggered just to refresh archive expiry when a source/manifest-verifiable copy already exists.

## Local PackLab-only disk-cleanup review (distinct from PL-0350 engineering)

Source: `coordination/sessions/M16-C001/PL-0350_DEFERRED_DISK_CLEANUP_REPORT_20261015.md`.

- C: free space **before** `91,608,444,928` bytes (**91.608 decimal GB**); **after** `91,448,082,432` (**91.448 GB**).
- **Actual net free-space change = -160,362,496 bytes (-0.160 GB)**. DO NOT claim 3.584 GB of actual recovered volume free space.
- Reported logical file lengths removed: **3,584,103,768 bytes = 3.584 decimal GB** from two clean, pushed inactive R08 Git worktrees (1.338 GB + 1.368 GB) and superseded cold Installer (0.878 GB). File-length accounting is not NTFS allocated/free-space accounting, and concurrent allocations may have masked the effect; no cause is proven.
- Unique PackLab-root logical scan shrank `43,787,156,239` to `40,203,052,471` bytes. Reported remaining PackLab-only AppData/OwnerDev tree **20.964 GB**, Codex artifacts **3.787 GB**, two preserved R07 worktrees **1.367 GB and 1.370 GB**. These are NOT automatically disposable.
- The clean R07 worktree's HEAD is not contained in `origin/main`; another has 2 local modifications. Both MUST stay until reconciled. Current managed worktree/owner checkout and working EXE protected.
- 11.58 MB of pytest fixture directories were blocked by system security policy; no bypass performed. This is not a credible explanation for the original ~119 GB free-space drop.
- Historical user report of ~200 GB free vs ~81.2 GB free is not reconciled by this **PackLab-only** scan or cleanup. On-disk evidence does not establish PackLab as cause of all ~119 GB. If user wishes, perform a **new read-only, whole-drive space attribution first**, no delete of other projects, no guessing and no forced quota.

**Cleanup audit disposition:** `SAFE_SCOPED_OPERATIONS_REPORTED / NO_VERIFIED_NET_DISK_RECOVERY`. Files inspected/protected/deleted not independently revalidated on owner Windows device; conclusions rely on builder report. No new deletion or cleanup action is authorized in this audit.

## Explicit exceptions / next boundaries

1. **Formal license/legal review remains PENDING.** The source/wheel/NOTICE/VC runtime and LGPL packaging matrix is engineering-cleared (zero unresolved machine checks), but this is not a lawyer's certification. Before conveying Installer/source to a different legal entity or rolling out to Kenya workstations, verify organizational authorization and actual license conditions. No blanket waiver. `legal_review_required=true`; `public_release_authorized=false`.
2. **No clean Windows target install independently proven:** hosted Windows installed smoke is PASS, but on-device/fresh-target install remains **PL-0351**, including signed Microsoft x64 VC runtime prereq, installer behavior, source/NOTICE content, admin privileges, safe user-data handling, uninstall/reinstall, GUI rendering, actual workflow opening and stability, different-PC controlled deployment. This is not a reason to undo PL-0350 engineering PASS.
3. **Cold vs warm size differs** but both have self-consistent SHA/installed smoke; preserve both reports and do not represent them as byte-identical. Commit built source unchanged.
4. **Private repository**, confirmed by authenticated repo API, matches owner's proprietary preference going forward. Previously public files may have been copied; do not imply they were recalled or that private alone establishes copyright ownership.
5. **Disk cleanup did not deliver more available volume space.** Need independent attribution, not deletion pressure. Working local warm Installer/SDK/OCP and owner assets must remain protected.

### Result

**PL-0350 ENGINEERING ACCEPTED.** Root `TASKS.md` may be updated by ChatGPT to mark engineering scope complete and transition to `PL-0351` controlled clean-PC acceptance planning, **without authorizing legal/public release or factory deployment**. The legal review/release gate remains open and separate. No more PL-0350 Rxx implementation prompts required.

Core sources:
- https://github.com/Sekiph82/PackLab/actions/runs/38646432056
- https://github.com/Sekiph82/PackLab/actions/runs/38649528145
- https://github.com/Sekiph82/PackLab/actions/runs/38646355410
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_ALL_REMAINING_WORK_ONE_SHOT_REPORT.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_DEFERRED_DISK_CLEANUP_REPORT_20261015.md
