# PL-0350 One-Shot Final Result Report

## Disposition

**PARTIAL / BLOCKED_OWNER_LEGAL_EVIDENCE — AWAITING_AUDIT**

The PL-0350 one-shot implementation and hosted packaging investigation are complete through the last authorized fail-closed boundary. The packaged Open3D load issue is fixed and the full no-network Studio smoke now passes. Redistribution clearance remains blocked by nine unresolved legal/provenance items. The workflow correctly skipped the Windows Installer and its downstream warm-cache proof. No audit pass, PL-0350 completion, installer, or public-release authorization is claimed.

## Source and validation

- Canonical repository: `Sekiph82/PackLab`, branch `main`.
- Final implementation source: `bb50690b8e932cbd8bb9f04504f36ed798698faa`.
- Latest hosted packaging run: [38617631153](https://github.com/Sekiph82/PackLab/actions/runs/38617631153), completed with failure at `Enforce redistribution clearance` only.
- Exact-SHA full Quality run: [38617544058](https://github.com/Sekiph82/PackLab/actions/runs/38617544058), success: lint, format, mypy, and `2,149 passed, 10 skipped, 1 deselected, 2 warnings`.
- The exact retained SDK checkpoint was restored, authenticated, validated and republished. Exact quarantined OCP runtime was restored and validated. OCP source compile was skipped. This packaging retry did not recompile OCCT or OCP.
- Packaging built successfully. Clean frozen NumPy 2.5.3 import, isolated Open3D 0.20.0 import/geometry capability probe, full offline Studio smoke, Qt staged-module contract, Open3D PE scan, and controlled OCP manifest checks all passed.

## Hosted artifacts

| Evidence | Run artifact | Size | SHA-256 |
| --- | --- | ---: | --- |
| Retained OCCT SDK | 11921297195 | 57,520,243 bytes | `a14f2660e3627b4ee88f7a7f1d6b4c66f9cdb2e6a9022990d64ba5d616a2ee72` |
| Controlled OCP runtime | 11922382361 | 46,462,994 bytes | `1a62424b85845eecd61be8a9706fb367258faaf8ae0dab63b2cbb7cfe1774e0b` |
| OCP source evidence | 11921068651 | 1,466 bytes | `3179d44b102a53960ba2f881d1330d3a5add61f6c0c7ec03931012598b4d88f4` |
| Open3D/Studio smoke diagnostics | 11922542537 | 3,625 bytes | `d1d1070fce37c108864c438284f8c4d150b41d3bd0b486ad141e454d03f1eb2e` |
| Redistribution pre-clearance evidence | 11922367788 | 305,713 bytes | `fd46a7e14299845b9f65055451b6549bc90de6c41ed2c3d43aa1a6d8fbf0ee02` |

## Installer and cache boundary

The compliance summary reports 479 staged files / 514,901,343 bytes, 123 collected notices against 61 required notices, 2 missing notices, 1 missing source package, 28 unresolved shipped files, 6 unresolved components, and 9 unresolved items. It sets `engineering_packaging_status=BLOCKED`, `legal_review_required=true`, and `public_release_authorized=false`.

The exact unresolved set is:

1. `component:microsoft-vc-runtime`
2. `component:open3d`
3. `component:packlab`
4. `component:pyside6-addons`
5. `component:pyside6-essentials`
6. `component:shiboken6`
7. `evidence:missing-notices`
8. `evidence:missing-source-packages`
9. `_internal/numpy.libs/msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll`

The OpenSSL provenance findings from the previous pass are cleared. PackLab's own rights/license disposition is absent; the exact Open3D wheel's complete native/transitive notice and source evidence is incomplete; the selected Qt/PySide/Shiboken LGPL/commercial route and module-specific licensing evidence are missing; and exact Microsoft redistribution entitlement for NumPy's hash-renamed VC runtime DLL has not been established. The owner/legal decisions and evidence cannot be inferred safely.

The fail-closed enforcement step failed as intended. Reviewed compliance-text injection, final compliance revalidation, Inno Setup installation, Installer build and Installer upload were skipped. Consequently, the prompt-dependent W08 cold-Installer-to-warm-cache proof was not eligible. SDK/OCP artifact restoration is verified; full W08 cache acceptance is **not**.

## Required owner/legal inputs to resume

- Authoritative PackLab license, redistribution and public-release disposition.
- Exact pinned Open3D wheel native/transitive component inventory, required notices, and any applicable source/relinking evidence.
- Qt/PySide/Shiboken module-specific SBOM/notices and selected, documented LGPL or commercial licensing route.
- Source-backed Microsoft entitlement for the exact staged hash-renamed VC runtime DLL, or an owner-approved packaging/runtime alternative.
- Complete missing notice and source-package evidence.

After those inputs are committed to the canonical repository, rerun the gated compliance/Installer chain and only then execute the required warm-cache proof.

## Owner checkout and governance

The owner Desktop checkout `C:\Users\sekip\Desktop\PackLab` remains untouched. At both inspections it had three, rather than ten, local changes: one tracked modification and two untracked files. Their recorded hashes were unchanged at completion. No reset, clean, rebase, stash or destructive checkout was run.

Root `TASKS.md`, frozen prompt and criteria were not modified. No `CHATGPT_AUDIT_VNN.md` was created. This report is builder evidence for independent audit; it is not project status or audit acceptance.
