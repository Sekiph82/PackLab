# M16-C001 - ChatGPT Partial Audit V03

Date: 2026-10-06
Decision: **AUDITED_PARTIAL_CHANGES_REQUIRED**

Independently accepted frontier: **PL-0347 V02 through PL-0348**
Reopened child: **PL-0349 V02**
Blocked downstream child: **PL-0350 V02**
PL-0351 through PL-0367: **NOT_STARTED**
PL-0368: **DEFERRED_POST_M17**

## Why the accepted frontier moved backward

PL-0349 V01 was initially accepted on the available hosted build/startup evidence.

PL-0350 V02 subsequently produced the first exact staged-file inventory. That new evidence proves the current production bundle omits two locked direct runtime dependencies:

- `cadquery-ocp-novtk==7.9.3.1.1` / `OCP`;
- `open3d==0.20.0`.

Both are dynamically imported in PackLab source, so PyInstaller's static discovery missed them while the startup smoke still passed.

The PL-0349 implementation prompt required required Python packages/resources to be present. Therefore the prior PL-0349 PASS is superseded by:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0349_CHATGPT_AUDIT_V02.md

Decision: `AUDITED_CHANGES_REQUIRED`.

PL-0347 V02 and PL-0348 remain independently accepted.

## PL-0350 V02

The redistribution gate stop remains correct and its diagnostic/compliance tooling is retained.

Independent artifact review confirmed:

- exact hosted stage: 283 files / 141,367,765 bytes;
- `unresolved_count=55`;
- 196 staged files carry unresolved status;
- seven unresolved component classes;
- installer and binary upload correctly blocked;
- only text/JSON/license evidence uploaded.

PL-0350 V02 audit:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_V02.md

## Required next order

The next execution order is:

1. **PL-0349 V02** — make the frozen production bundle capability-complete for required locked in-process dependencies;
2. **PL-0350 V03** — rerun redistribution inventory against that corrected bundle and close only the actual shipped surface;
3. if PL-0350 V03 is green, continue PL-0351 through PL-0367 in order;
4. PL-0368 remains `DEFERRED_POST_M17`.

## Frozen packaging completeness rules

PL-0349 V02 must prove the frozen executable itself has:

- PackLab Qt GUI startup;
- OCP/CAD binding AVAILABLE;
- Open3D 0.20.0 AVAILABLE;
- bounded CAD smoke;
- bounded Open3D geometry smoke;
- no runtime download.

Required direct runtime dependencies cannot be omitted merely to simplify redistribution.

## Frozen PL-0350 V03 reduction strategy

The compliance surface should be reduced truthfully before adding more notices:

### Qt/PySide

- Replace the broad `PySide6` meta dependency with the exact minimal community package set required by actual PackLab imports when technically compatible, preferably `PySide6-Essentials==6.11.2`.
- Repository-wide import evidence must justify every retained Qt module.
- Do not ship unused Addons modules.
- Under the currently evidenced open-source route, fail closed if any GPL-only Qt module is staged.
- In particular, Qt Virtual Keyboard must not be present unless separate commercial/GPL-compatible authority exists.
- Keep Qt libraries dynamically replaceable; no static Qt linking.
- Collect exact LGPL/GPL/module third-party notice evidence for only the retained modules/plugins.
- Release-time Qt source availability remains an explicit downstream release gate; PL-0350 must not claim legal approval.

### Windows runtime

Do not redistribute runner/system DLLs merely because PyInstaller collected them.

For the supported Windows baseline, prefer:

- OS-provided API-set/UCRT components as external operating-system prerequisites;
- external Microsoft Visual C++ Redistributable prerequisite rather than bundled MSVC runtime DLLs.

Any removed runtime file must be backed by a fresh hosted packaged capability smoke after pruning. Installer preflight/documentation must state the required VC runtime, and must not silently download it.

### CPython / OpenSSL

- map `base_library.zip` to CPython runtime;
- map Python-distributed `libcrypto-3-x64.dll` / `libssl-3-x64.dll` to exact OpenSSL version/build evidence;
- include exact required OpenSSL license/notice evidence.

### PyInstaller hooks

Do not mark the entire `pyinstaller-hooks-contrib` package as a shipped runtime component merely because analysis-time hooks ran.

- standard hooks are build-time analysis inputs;
- only actual runtime hooks embedded into the executable are shipped runtime content;
- runtime hook licensing must be mapped per exact embedded hook.

### OCP/OCCT and Open3D

Once PL-0349 V02 stages them:

- OCP binding and OCCT native kernel remain separate license units;
- every staged OCP/OCCT native file must be inventory-mapped;
- Open3D main and staged third-party/native contents must be mapped to exact reviewed evidence;
- inability to close either surface remains a hard stop.

## Authority note

This compliance work is an engineering evidence and packaging gate, not legal advice or a legal-compliance certification. Final public release remains gated by later M16/M17 release checks and owner/legal judgment where appropriate.

## Verdict

`AUDITED_PARTIAL_CHANGES_REQUIRED`

Resume at PL-0349 V02, then PL-0350 V03. Do not start PL-0351 until both are builder-green.
