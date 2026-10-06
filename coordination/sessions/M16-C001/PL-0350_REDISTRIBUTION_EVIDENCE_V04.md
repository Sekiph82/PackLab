# PL-0350 V04 - Hosted Redistribution Evidence

Date: 2026-10-06

Build revision: `234c212bb0fccf7fc9e22f97ef5a643cfde594b2`

Workflow: [PackLab Studio Windows Build run 37481126993](https://github.com/Sekiph82/PackLab/actions/runs/37481126993)

Pre-clearance evidence artifact: [artifact 11420659070](https://github.com/Sekiph82/PackLab/actions/runs/37481126993/artifacts/11420659070)

Artifact SHA-256: `a646f5db38f4cfd404e9a8985e831a4267c9d94edeaed6cb2a76473615821fd4`

Artifact size: 290,304 bytes; one-day retention; text/JSON/license evidence only.

## Hosted result

The clean Windows hosted build, approved Qt-surface assertion, and packaged no-network capability smoke passed. The capability smoke checked `qt_studio_gui`, `qt_vector_pdf`, `ocp_cad`, and `open3d_geometry`. The exact hosted inventory and clearance gate then returned:

| Measure | Hosted result |
| --- | ---: |
| Staged files | 511 |
| Staged bytes | 531,589,169 |
| Unresolved shipped-file rows | 115 |
| Unresolved components | 5 |
| Total unresolved items | 6 |
| Missing notice sets | 0 |
| Missing source-package evidence | 5 |
| Forbidden Qt components | 0 |
| External prerequisites | 1 |
| Engineering packaging status | `BLOCKED` |
| Legal review required | `true` |
| Public release authorized | `false` |

The 115 unresolved file rows inherit unresolved ownership from the five component gates. The sixth unresolved item is missing exact native source-package evidence. The installer clearance step failed closed; no installer, final compliance artifact, or source archive artifact was produced.

## Closed mappings and runtime changes

- The generated `qt-staged-surface.json` and `windows-runtime-capabilities.json` are PackLab-owned records bound to build revision `234c212bb0fccf7fc9e22f97ef5a643cfde594b2` and Studio `0.1.0`.
- PyInstaller `base_library.zip` is mapped to the CPython 3.12 runtime and PSF license evidence.
- CPython's `libcrypto-3.dll` and `libssl-3.dll` are mapped separately to OpenSSL 3.0.16. Their hosted SHA-256 values are `ccfffddcd3defb8d899026298af9af43bc186130f8483d77e97c93233d5f27d7` and `007142039f04d04e0ed607bda53de095e5bc6a8a10d26ecedde94ea7d2d7eefe`. The OpenSSL 3.0.16 Apache-2.0 text and official source archive URL/hash are pinned in the registry. The source archive itself was not included because clearance remained blocked.
- The production stage contains zero root `api-ms-win-*`, `VCRUNTIME140*.dll`, or `ucrtbase.dll` files, and zero unrelated `libcrypto-3-x64.dll` / `libssl-3-x64.dll` files.
- Wheel-private Qt/Shiboken runtime copies remain staged. The new x64 Microsoft VC++ prerequisite manifest states a minimum version of 14.44.35211, registry detection, and no automatic download. Inno Setup now rejects a missing or older prerequisite.
- These removals and the retained wheel-private runtime surface passed the hosted Qt/PDF/OCP/Open3D smoke. This does not substitute for the clean installed-artifact portability smoke.

## Remaining exact blockers

- `cadquery-ocp-novtk==7.9.3.1.1`: retained OCCT and bundled third-party native files still lack complete per-file upstream/version/license/notice/source mappings.
- `open3d==0.20.0`: `Open3D.dll`, the Python binding, TBB, and static third-party composition still lack exact wheel/build-source evidence and notices.
- `pyside6-addons==6.11.2`, `pyside6-essentials==6.11.2`, and `shiboken6==6.11.2`: exact staged-module/source archive mapping and the QtPdf/PDFium third-party notice set are incomplete.
- Five source-package evidence requirements remain unresolved across those owners. No legal certification is claimed.

Because these gates remain unresolved, PL-0351 clean-install portability smoke was not started. This includes the permanent regression check for the user's repeated `QtCore` loader error (“The specified procedure could not be found”). The successful hosted build smoke is not evidence that a clean installed artifact passes that check.

## Referenced upstream evidence

- [Qt PDF licensing and third-party components](https://doc.qt.io/QT-6/qtpdf-licensing.html)
- [Qt for Python 6.11.2 source archive mirror list](https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.11.2-src/pyside-setup-everywhere-src-6.11.2.zip.mirrorlist)
- [OpenSSL 3.0.16 official source release](https://github.com/openssl/openssl/releases/tag/openssl-3.0.16)
- [OpenSSL 3.0.16 license text](https://github.com/openssl/openssl/blob/openssl-3.0.16/LICENSE.txt)
- [Microsoft supported Visual C++ Redistributable downloads](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170)
- [Open3D 0.20.0 third-party inventory](https://github.com/isl-org/Open3D/blob/v0.20.0/3rdparty/README.md)

## Scope and disposition

This is implementation evidence, not an independent audit or legal opinion. No root `TASKS.md`, audit verdict, tag, release, signing claim, or PL-0351+ implementation was created. The batch stops at PL-0350 V04 pending independent milestone audit and the exact unresolved redistribution evidence.
