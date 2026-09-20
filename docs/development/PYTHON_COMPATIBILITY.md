# Python compatibility decision

Decision checked: **2026-09-20**. PackLab pins exactly **CPython 3.12.10** in `.python-version`.

## Why 3.12.10

3.12 is the strongest current intersection for the Windows-first Studio foundation. Python 3.12 supports the governed Windows baseline, and Python 3.12.10 was the final regular 3.12 release with binary installers. Later 3.12 security releases remain source-only, so the patch pin favors a reproducible Windows bootstrap while preserving the 3.12 ABI compatibility of the selected ecosystem.

The decision was checked against these upstream sources:

- [CPython 3.12.14 release](https://www.python.org/downloads/release/python-31214/) and [PEP 693 release schedule](https://peps.python.org/pep-0693/) — 3.12 security lifecycle and 3.12.10 as the last regular binary-installer release.
- [PySide6 6.11.2 on PyPI](https://pypi.org/project/PySide6/) — current metadata requires Python `>=3.10,<3.15` and publishes Windows `cp310-abi3` wheels.
- [Open3D 0.20.0 on PyPI](https://pypi.org/project/open3d/0.20.0/) — tested Python 3.10–3.13 range and a Windows CPython 3.12 wheel.
- [OpenCV Python on PyPI](https://pypi.org/project/opencv-python/) — Windows classifiers and Python `>=3.6` package metadata.
- [PyTorch Windows installation guidance](https://docs.pytorch.org/get-started/locally/) — Windows support currently lists Python 3.9–3.12.
- [PackLab dependency/license register](../architecture/DEPENDENCY_LICENSE_REGISTER.md) — the Python OpenCascade binding remains `TBD / NOT SELECTED` and is not chosen here.

## Compatibility boundary

The metadata supports selecting 3.12.10 as the project interpreter. It does not prove that every future dependency combination, GPU/CUDA build, external executable, or packaged application is integrated. PL-0029 owns dependency locking/bootstrap; later tasks own actual PySide6, Open3D, OpenCV, PyTorch, engine, and runtime integration validation. The Python OpenCascade binding choice remains owned by PL-0289 and must not be inferred from OCCT itself.
