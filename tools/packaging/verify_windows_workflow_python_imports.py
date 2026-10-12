"""Smoke-test repository-local Python CLIs used by the Windows build workflow."""

from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
from pathlib import Path

MODULE_CALL = re.compile(
    r"(?<![\w.])python(?:\.exe)?(?:\s+-S)?\s+-m\s+(tools\.packaging\.[A-Za-z_]\w*)",
    re.IGNORECASE,
)
SCRIPT_CALL = re.compile(
    r"(?<![\w.])python(?:\.exe)?(?:\s+-[A-Za-z][A-Za-z0-9_-]*)*\s+"
    r"(?:['\"])?(?:\.?[\\/])?tools[\\/]packaging[\\/]"
    r"([A-Za-z_]\w*)\.py\b",
    re.IGNORECASE,
)
REPRODUCER = "tools.packaging.fetch_verify_windows_native_sources"
REPRODUCER_SCRIPT = Path("tools/packaging/fetch_verify_windows_native_sources.py")


def _clean_python_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment["PYTHONNOUSERSITE"] = "1"
    return environment


def _run_module(root: Path, module: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-S", "-m", module, "--help"],
        cwd=root,
        env=_clean_python_environment(),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _repository_importing_modules(root: Path) -> set[str]:
    modules: set[str] = set()
    for script in sorted((root / "tools/packaging").glob("*.py")):
        tree = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        imports_tools = any(
            (
                isinstance(node, ast.Import)
                and any(
                    alias.name == "tools" or alias.name.startswith("tools.") for alias in node.names
                )
            )
            or (
                isinstance(node, ast.ImportFrom)
                and node.level == 0
                and (
                    node.module == "tools" or bool(node.module and node.module.startswith("tools."))
                )
            )
            for node in ast.walk(tree)
        )
        if imports_tools:
            modules.add(f"tools.packaging.{script.stem}")
    return modules


def verify_workflow_imports(root: Path) -> list[str]:
    workflow_path = root / ".github/workflows/windows-studio-build.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    direct_calls = SCRIPT_CALL.findall(workflow)
    if direct_calls:
        raise RuntimeError(
            "Windows workflow invokes repository scripts by file path: "
            + ", ".join(sorted(set(direct_calls)))
        )

    modules = sorted(set(MODULE_CALL.findall(workflow)) | _repository_importing_modules(root))
    if not modules:
        raise RuntimeError("Windows workflow has no repository-local package module calls")

    script_probe = subprocess.run(
        [sys.executable, "-S", str(root / REPRODUCER_SCRIPT), "--help"],
        cwd=root,
        env=_clean_python_environment(),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if script_probe.returncode == 0 or "No module named 'tools'" not in script_probe.stderr:
        raise RuntimeError(
            "Direct-file regression probe did not reproduce the expected missing-tools import: "
            f"exit={script_probe.returncode}; stderr={script_probe.stderr.strip()}"
        )
    print("SCRIPT_PATH_REPRODUCER_PASS exit=1 missing=tools")

    module_probe = _run_module(root, REPRODUCER)
    if module_probe.returncode != 0:
        raise RuntimeError(
            f"Corrected module invocation failed for {REPRODUCER}: "
            f"exit={module_probe.returncode}; stderr={module_probe.stderr.strip()}"
        )

    for module in modules:
        result = _run_module(root, module)
        if result.returncode != 0:
            raise RuntimeError(
                f"Workflow module --help failed for {module}: "
                f"exit={result.returncode}; stderr={result.stderr.strip()}"
            )
        print(f"WORKFLOW_MODULE_IMPORT_PASS {module} exit={result.returncode}")

    print(f"WORKFLOW_PYTHON_IMPORT_SMOKE_PASS count={len(modules)}")
    return modules


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[2]
    modules = verify_workflow_imports(root)
    print("Workflow package modules:", ", ".join(modules))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
