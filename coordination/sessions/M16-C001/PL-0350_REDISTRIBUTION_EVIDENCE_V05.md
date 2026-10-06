# PL-0350 V05 — Hosted Pre-clearance Evidence

Date: 2026-10-06

Build revision: `7a6e6be4224d241c14b57f3d00ed1b306ae3043c`

Windows workflow: [run 37492304087](https://github.com/Sekiph82/PackLab/actions/runs/37492304087)

Text-only pre-clearance artifact: [artifact 11425738670](https://github.com/Sekiph82/PackLab/actions/runs/37492304087/artifacts/11425738670)

Artifact: `packlab-windows-compliance-preclearance-7a6e6be4224d241c14b57f3d00ed1b306ae3043c` — 290,305 bytes, one-day retention.

## Hosted result

The fresh `windows-latest` run passed the lock/install, PyInstaller staging build, approved Qt surface assertion, and packaged no-network capability smoke groups `qt_studio_gui`, `qt_vector_pdf`, `ocp_cad`, and `open3d_geometry`. The exact staging inventory was uploaded as text-only evidence. The clearance gate then failed closed.

| Measure | Hosted result |
| --- | ---: |
| Staged files | 511 |
| Staged bytes | 531,590,047 |
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

Per-component native file frontier remains the V04 baseline: OCP 79, Open3D 3, PySide6 Essentials 24, PySide6 Addons 2, and Shiboken6 6; the remaining row is the composite `PackLabStudio.exe`. The five unresolved component IDs are `cadquery-ocp-novtk==7.9.3.1.1`, `open3d==0.20.0`, `pyside6-addons==6.11.2`, `pyside6-essentials==6.11.2`, and `shiboken6==6.11.2`.

Hosted evidence file hashes:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `compliance-validation.json` | 797 | `b0532846636bc3cac3be123757b04445c2cb692e6ac711e3266eaaa6b38b4e7c` |
| `windows-component-summary.json` | 34,102 | `f1136765103ff09874d0418f6a3b49c85cfd59ab7238a5e58df8de286055fbc1` |
| `windows-redistribution-inventory.json` | 474,252 | `215708f3e095988940598eb1ae403e17dc869f199297ad5fbab70a2fad1e1df3` |
| `license-evidence-manifest.json` | 34,250 | `2a4d870f1a8e978e64fd9d7436eee79ab16db7f86f7a8d23daf17e56078afd2e` |
| `THIRD_PARTY_NOTICES.txt` | 16,067 | `f9a754d558385c9a41c62012d6ac21bd37d62165b099df32d326b4ed6ffabaa7` |

## Exact provenance blocker

Inspection of the OCP source at the registry-pinned commit [`d69b064a3a604ebf245b1f3b14fb54c835a3a571`](https://github.com/CadQuery/OCP/tree/d69b064a3a604ebf245b1f3b14fb54c835a3a571) confirmed:

- `conda/meta.yaml` pins `OCCT_VER` to `7.9.3`, but resolves the conda dependency as `occt=7.9.3=all*`;
- `environment.devenv.yml` also uses `occt=7.9.3=all*` and does not pin the exact conda build or transitive native package set;
- the exact staged OCP wheel's `DELVEWHEEL` file records delvewheel `1.12.1` and its repair invocation, but no per-DLL source component/version manifest;
- the wheel and staged inventory contain bundled native libraries including FreeImage, FreeType, OpenEXR-family, JPEG, LittleCMS, Lerc, LZMA, PNG, WebP, OpenJPEG/OpenJPH, RAW, TIFF, zlib/deflate, zstd, and wheel-private Microsoft runtimes.

These inputs establish the OCCT version and exact staged bytes, but do not establish each bundled third-party DLL's source project, exact version/build, license route, or corresponding source archive. A basename-derived or guessed mapping would violate PL-0350 V05. No OCP rows were assigned fabricated per-file provenance; the three required exact native maps were not represented as complete or clearance-ready.

The hosted V05 run did not download or verify the required source package set. In particular, the five source-package gates remain open, QtPdf/PDFium third-party notices have not been closed, and Open3D static native composition remains unverified. The hosted evidence is not a clearance result.

## OWNER DEV acceptance and downstream gates

The integrated OWNER DEV repair was published in commits `e3afc614e80223fdcffec605d58416555200f9d9` and `7a6e6be4224d241c14b57f3d00ed1b306ae3043c`. Refresh from the latter returned `OWNER_DEV_READY`.

The actual Desktop `PackLab.lnk` was invoked using the Shell `open` verb. The visible `PackLab Studio` window stayed alive continuously for 15.02 seconds, reported a nonzero window icon handle (`566102553`), and was then closed with `WM_CLOSE`. Desktop and Start Menu shortcuts both resolved to `%LOCALAPPDATA%\PackLab\OwnerDev\branding\PackLab.ico`; its SHA-256 was `a4a655fc92796413130633703602885671f5b1a0773d045ebc79d6bd522c7fc1`.

PL-0351 was not started because PL-0350 remains blocked. The owner-observed installed-artifact `QtCore` loader error has not been verified or fixed by this source-mode launcher acceptance.

No installer, source archive artifact, tag, GitHub Release, signing claim, V0.1 publication, M17 work, or PL-0368 work was produced.
