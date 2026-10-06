"""Fail closed when the staged Qt module/plugin surface exceeds PackLab's contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def inspect_stage(
    stage: Path,
    contract_path: Path,
    build_revision: str | None = None,
    studio_version: str | None = None,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    approved = set(contract["direct_modules"]) | set(contract["transitive_modules"])
    modules: set[str] = set()
    plugins: set[str] = set()
    native_modules: set[str] = set()
    forbidden_patterns = [
        re.compile(re.escape(name), re.IGNORECASE) for name in contract["forbidden_module_families"]
    ]
    for file in stage.rglob("*"):
        if not file.is_file():
            continue
        relative = file.relative_to(stage).as_posix()
        folded = relative.casefold()
        if file.name.casefold().startswith("icu") and file.suffix.casefold() == ".dll":
            raise ValueError("unrelated ICU runtime DLL is staged")
        if any(pattern.search(relative) for pattern in forbidden_patterns):
            raise ValueError("forbidden Qt module family is staged")
        if file.name.casefold().startswith("qt6") and file.suffix.casefold() == ".dll":
            allowed_native = {value.casefold() for value in contract["native_module_dlls"]}
            if file.name.casefold() not in allowed_native:
                raise ValueError("unapproved Qt native module DLL is staged")
            native_modules.add(file.name)
        parts = folded.split("/")
        if "pyside6" in parts and folded.endswith(".pyd"):
            module = f"PySide6.{file.stem}"
            if module not in approved:
                raise ValueError("unapproved PySide6 extension module is staged")
            modules.add(module)
        if "pyside6" in parts and parts[
            parts.index("pyside6") + 1 : parts.index("pyside6") + 2
        ] == ["plugins"]:
            plugin = "/".join(parts[parts.index("pyside6") + 2 :])
            if plugin not in {value.casefold() for value in contract["plugin_allowlist"]}:
                raise ValueError("unapproved Qt plugin is staged")
            plugins.add(plugin)
        if "virtualkeyboard" in folded or "qtvirtualkeyboard" in folded:
            raise ValueError("Qt Virtual Keyboard is staged")
        path_parts = folded.split("/")
        if "open3d" in path_parts:
            package_tail = path_parts[path_parts.index("open3d") + 1 :]
            if any(
                part
                in {"examples", "labextension", "nbextension", "agent_skills", "tools", "_ml3d"}
                for part in package_tail
            ) or folded.endswith(".ipynb"):
                raise ValueError("Open3D development or notebook content is staged")
    missing = set(contract["direct_modules"]) - modules
    if missing:
        raise ValueError("required Qt extension module is missing")
    result: dict[str, object] = {
        "schema_version": 1,
        "status": "PASS",
        "approved_staged_modules": sorted(modules),
        "approved_staged_plugins": sorted(plugins),
        "approved_staged_native_modules": sorted(native_modules),
        "forbidden_module_families_absent": True,
        "unrelated_icu_runtime_dlls_absent": True,
    }
    if build_revision is not None:
        if not re.fullmatch(r"[0-9a-f]{40}", build_revision):
            raise ValueError("invalid build revision")
        result["PACKLAB_BUILD_REVISION"] = build_revision
    if studio_version is not None:
        if not re.fullmatch(
            r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?", studio_version
        ):
            raise ValueError("invalid Studio version")
        result["studio_version"] = studio_version
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--build-revision")
    parser.add_argument("--studio-version")
    args = parser.parse_args()
    try:
        result = inspect_stage(args.stage, args.contract, args.build_revision, args.studio_version)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Qt staged surface assertion failed ({type(error).__name__}).")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
