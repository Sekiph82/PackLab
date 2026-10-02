# PL-0225 Open3D Windows / Python 3.12 Artifact and License Evidence V01

Date: 2026-10-02
Purpose: exact dependency/build evidence for the PL-0225 PackLab geometry-analysis adapter.

## Selected artifact

- Distribution: `open3d==0.20.0` (exact pin in `pyproject.toml` and `uv.lock`).
- Artifact: `open3d-0.20.0-cp312-cp312-win_amd64.whl` from the [PyPI 0.20.0 release](https://pypi.org/project/open3d/0.20.0/).
- Official Open3D v0.20 release notes publish the Windows CPython 3.12 wheel and state that the standard Windows `open3d` package is the CPU build: https://github.com/isl-org/Open3D/releases/tag/v0.20.0
- Wheel size: `77,497,277` bytes.
- Wheel SHA-256: `60010f21d44f13557ba007893bc13a69827faa4dc49eedd923d1397096c20d92`.
- The exact wheel was downloaded to a temporary directory, its SHA-256 was checked, and its metadata and archive contents were inspected. `uv.lock` records the selected package and artifact hashes for reproducible installation.
- The wheel metadata declares MIT and contains `open3d-0.20.0.dist-info/licenses/LICENSE.txt` with the Open3D MIT license.

## Runtime proof in PackLab's locked environment

Environment: CPython `3.12.10`, Windows 11 x86-64, project `.venv`, after adding the exact pin and running `uv sync --locked`.

Observed build configuration:

| Field | Observed value |
|---|---|
| `BUILD_TENSORFLOW_OPS` | `false` |
| `BUILD_PYTORCH_OPS` | `true` |
| `Pytorch_VERSION` | `2.13.0+cpu` |
| `BUILD_CUDA_MODULE` | `false` |
| `BUILD_SYCL_MODULE` | `false` |
| `BUILD_SHARED_LIBS` | `true` |
| `BUILD_GUI` | `true` |
| `BUILD_JUPYTER_EXTENSION` | `true` |
| `BUNDLE_OPEN3D_ML` | `true` |
| `CMAKE_BUILD_TYPE` | `Release` |

The direct package import reported version `0.20.0`. Actual point-cloud and triangle-mesh construction/copy round-trips succeeded in the locked PackLab Python environment. `uv pip check --python .venv/Scripts/python.exe` reported all installed packages compatible. No GUI, CUDA, SYCL, PyTorch runtime or sensor capability is claimed by these checks.

The adapter imports only the installed module and package metadata. It has no subprocess, installer, HTTP or auto-download fallback. Missing imports report `UNAVAILABLE`; import/build/version ambiguity reports `UNKNOWN`.

## Artifact contents and bundled component notices

The inspected Windows wheel contains these native files:

| File | Evidence |
|---|---|
| `open3d/Open3D.dll` | Open3D native runtime |
| `open3d/open3d_torch_ops.dll` | Present in the wheel; build config reports `BUILD_PYTORCH_OPS=true` and `Pytorch_VERSION=2.13.0+cpu`. This does not add or claim an installed Python `torch` runtime. |
| `open3d/pybind.cp312-win_amd64.pyd` | CPython 3.12 Windows x86-64 binding |
| `open3d/tbb12.dll` | File version `2021.12.0`; oneTBB `v2021.12.0` is Apache-2.0: https://github.com/oneapi-src/oneTBB/blob/v2021.12.0/LICENSE.txt |

The wheel's Jupyter extension `third-party-licenses.json` identifies `lodash 4.18.1` (MIT), `sdp 2.12.0` (MIT), and `webrtc-adapter 4.2.2` (BSD-3-Clause). The file is retained inside the wheel; Open3D itself also includes a `Roboto-License.txt` resource license.

The Open3D v0.20.0 source tree publishes a pinned [third-party library inventory](https://github.com/isl-org/Open3D/blob/v0.20.0/3rdparty/README.md), including Apache-2.0, BSD, MIT, zlib, MPL-2.0, and LGPL-3.0-with-static-link-exception components. The wheel exposes several compiled native files but does not include a complete per-binary static-link manifest. The source inventory is therefore preserved as build-compliance evidence, while the precise static native composition remains a redistribution review item. This record does not grant distribution approval.

## Resolved Python package license metadata

Adding Open3D produced 76 package records in `uv.lock`, of which 51 are new package records relative to the prior lock. On this Windows CPython 3.12 environment, the locked dependency resolution installed 49 of those new distributions; `pexpect` and `ptyprocess` are non-Windows conditional lock entries. Names, versions and license declarations below were read from the matching PyPI release metadata on 2026-10-02. The exact versions and file hashes remain in `uv.lock`.

| Distribution | Version | PyPI license declaration |
|---|---:|---|
| annotated-types | 0.8.0 | MIT |
| asttokens | 3.0.2 | Apache 2.0 |
| blinker | 1.9.0 | MIT License |
| certifi | 2026.7.22 | MPL-2.0 |
| charset-normalizer | 3.5.2 | MIT |
| click | 8.5.0 | BSD-3-Clause |
| comm | 0.2.3 | BSD 3-Clause License |
| configargparse | 1.8.0 | MIT |
| dash | 4.4.1 | MIT |
| executing | 2.2.1 | MIT |
| fastjsonschema | 2.22.2 | BSD-3-Clause |
| flask | 3.1.3 | BSD-3-Clause |
| idna | 3.20 | BSD-3-Clause |
| importlib-metadata | 9.0.1 | Apache-2.0 |
| ipython | 9.17.1 | BSD-3-Clause |
| ipython-pygments-lexers | 1.1.1 | BSD License |
| ipywidgets | 8.1.9 | BSD 3-Clause License |
| itsdangerous | 2.2.0 | BSD License |
| janus | 2.0.0 | Apache 2 |
| jedi | 0.20.0 | MIT |
| jinja2 | 3.1.6 | BSD License |
| jupyter-core | 5.9.1 | BSD-3-Clause |
| jupyterlab-widgets | 3.0.17 | BSD License; distribution also contains its own bundled JavaScript notices |
| markupsafe | 3.0.3 | BSD-3-Clause |
| matplotlib-inline | 0.2.2 | BSD-3-Clause |
| narwhals | 2.26.0 | MIT |
| nbformat | 5.11.1 | BSD 3-Clause License |
| nest-asyncio | 1.6.0 | BSD |
| numpy | 2.5.3 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| open3d | 0.20.0 | MIT |
| parso | 0.8.7 | MIT |
| pexpect | 4.9.0 | ISC license (non-Windows marker) |
| platformdirs | 4.12.2 | MIT |
| plotly | 7.1.0 | MIT |
| prompt-toolkit | 3.0.53 | BSD License |
| psutil | 7.2.2 | BSD-3-Clause |
| ptyprocess | 0.7.0 | ISC License (non-Windows marker) |
| pure-eval | 0.2.4 | MIT |
| pydantic | 2.13.5 | MIT |
| pydantic-core | 2.46.5 | MIT |
| requests | 2.34.2 | Apache-2.0 |
| retrying | 1.4.2 | Apache-2.0 |
| setuptools | 84.0.0 | MIT |
| stack-data | 0.6.3 | MIT |
| traitlets | 5.16.1 | BSD 3-Clause License |
| typing-inspection | 0.4.4 | MIT |
| urllib3 | 2.8.0 | MIT |
| wcwidth | 0.9.1 | MIT License |
| werkzeug | 3.1.9 | BSD-3-Clause |
| widgetsnbextension | 4.0.16 | BSD 3-Clause License |
| zipp | 4.1.0 | MIT |

This inventory records upstream package declarations and the exact lock resolution; it is not legal advice. It does not authorize redistribution of Open3D or PackLab. Preserve applicable dependency notices and repeat component-level review against any future wheel/build or distribution bundle.
