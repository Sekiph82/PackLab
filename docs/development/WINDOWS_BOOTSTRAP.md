# Windows bootstrap

PackLab uses [uv](https://docs.astral.sh/uv/) for public, reproducible Python environment management in M01. `uv.lock` is the generated exact resolution for the root project and its M01 development group. The project pin is CPython `3.12.10`; the bootstrap validation tool is `uv 0.11.26`.

## Use

From a PowerShell terminal at the repository root:

```powershell
.\scripts\bootstrap_windows.ps1
```

The script validates Python, uv, `pyproject.toml`, `uv.lock`, and `.python-version` before running `uv sync --locked --dev`. Re-running it is safe: uv reconciles the existing project environment to the committed lock and the script does not remove owner data. Version or file mismatches fail before installation.

## Locked scope

The lock contains only the M01 developer tools declared in the root project: pytest, Ruff, and mypy plus their transitive packages. It does not select PySide6, Open3D, OpenCV, PyTorch, COLMAP, OpenMVS, Blender, a CUDA runtime, or a Python OpenCascade binding. The latter remains `TBD / NOT SELECTED` for PL-0289.

The checked tool provenance is uv `0.11.26` from the public uv distribution, with the exact resolved package versions and hashes recorded in `uv.lock`. The developer tools are used for local quality/test workflow; their package licenses remain subject to the existing dependency/license register and release review. No credentials, absolute owner paths, private indexes, or installation commands are embedded.

This bootstrap is Windows-focused and does not claim macOS/Xcode, physical-device, CUDA, or external-engine validation.
