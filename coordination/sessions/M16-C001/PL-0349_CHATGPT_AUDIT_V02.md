# PL-0349 - ChatGPT Independent Audit V02

Date: 2026-10-06
Decision: **AUDITED_CHANGES_REQUIRED**
Supersedes: **PL-0349_CHATGPT_AUDIT_V01.md**
Task: **Windows PackLab Studio production build completeness**

## Why the prior PASS is superseded

PL-0349 V01 correctly proved that the real Studio entry point could be frozen, started, and smoke-tested. At that time the available evidence did not include the exact staged file inventory.

PL-0350 V02 has now produced the first exact hosted staging inventory for that same production build. That new evidence changes the audit result.

The PL-0350 hosted compliance artifact for build revision `397786cac0cf276d1ebd5a27e0fc6c77e07619b9` inventories 283 staged files. It contains **no staged component mapping for either**:

- `cadquery-ocp-novtk==7.9.3.1.1` / top-level `OCP`;
- `open3d==0.20.0`.

Both are direct runtime dependencies in `pyproject.toml`.

The source explains why PyInstaller missed them:

- `cad_adapter.py` loads OCP modules dynamically with `importlib.import_module("OCP...")`;
- `geometry_adapter.py` loads Open3D dynamically with `importlib.import_module("open3d")`.

A startup-only Qt smoke therefore cannot prove these production capabilities are present.

PL-0349's frozen implementation prompt explicitly required the production build to include required Python packages/resources. The new exact staging evidence proves that requirement is not yet met.

## Retained accepted work

The following PL-0349 work remains valid and should be preserved:

- real `packlab_studio.app:main` production entry point;
- pinned/reviewed PyInstaller build tooling;
- path-free build revision + Studio version provenance;
- frozen resource resolution;
- no-network Qt application startup smoke;
- private/checkpoint/external-engine exclusion checks;
- hosted Windows build infrastructure.

## Required remediation

PL-0349 V02 must make the packaged production application capability-complete for the locked in-process runtime dependencies before redistribution review continues.

At minimum the packaged smoke must prove, from the **frozen executable environment**:

1. PySide/Qt application startup;
2. OCP/cadquery-ocp-novtk import and PackLab CAD runtime capability probe is AVAILABLE;
3. Open3D 0.20.0 import and PackLab geometry capability probe is AVAILABLE;
4. a bounded minimal CAD operation succeeds through the packaged OCP seam;
5. a bounded minimal Open3D conversion/geometry operation succeeds through the packaged adapter;
6. no hidden runtime download is used.

The packaging implementation may add explicit hidden-import/binary/data collection rules for dynamically imported packages. It must not satisfy this by weakening capability probes or converting required capabilities to optional.

## Verdict

`AUDITED_CHANGES_REQUIRED`

Accepted M16 frontier is therefore rolled back to PL-0348. Resume with PL-0349 V02, then rerun PL-0350 compliance against the corrected capability-complete bundle.
