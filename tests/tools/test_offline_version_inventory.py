"""Offline, stdlib-only checks; no CI or package installation needed."""

from __future__ import annotations

import json
import plistlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.release.offline_version_inventory import (
    SourceVersionError,
    _verify_checkout_commit,
    inventory,
    release_train_identity,
)

ROOT = Path(__file__).resolve().parents[2]
APP = "apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj"
INFO = "apps/ios-capture/PackLabCapture/Info.plist"
STUDIO = "apps/windows-studio/src/packlab_studio/__init__.py"
SCHEMA = "schemas/packscan/manifest.schema.json"
SCHEMA_CODE = "core/src/packlab_core/packscan/container.py"


def _write(root: Path, rel: str, content: bytes) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def _project(debug_version: str = "0.1.0", release_version: str = "0.1.0") -> str:
    blocks = []
    for name, version in (("Debug", debug_version), ("Release", release_version)):
        blocks.append(
            f"/* {name} */ = {{isa = XCBuildConfiguration; buildSettings = {{ "
            f"MARKETING_VERSION = {version}; CURRENT_PROJECT_VERSION = 1; "
            f"PRODUCT_BUNDLE_IDENTIFIER = com.packlab.capture; "
            f"}}; name = {name}; }};"
        )
    # Test target must never be mistaken for Capture's bundle.
    blocks.append(
        "/* Debug */ = {isa = XCBuildConfiguration; buildSettings = { "
        "PRODUCT_BUNDLE_IDENTIFIER = com.packlab.capture.tests; "
        "}; name = Debug; };"
    )
    return "\n".join(blocks)


def _make_fixture(root: Path) -> None:
    _write(root, "pyproject.toml", b'[project]\nname = "packlab"\nversion = "0.1.0"\n')
    _write(root, STUDIO, b'__version__ = "0.1.0"\n')
    _write(root, APP, _project().encode("utf-8"))
    _write(
        root,
        INFO,
        plistlib.dumps(
            {
                "CFBundleShortVersionString": "$(MARKETING_VERSION)",
                "CFBundleVersion": "$(CURRENT_PROJECT_VERSION)",
                "CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
            }
        ),
    )
    _write(
        root,
        SCHEMA,
        json.dumps({"properties": {"schema_version": {"const": "1.0.0"}}}).encode(),
    )
    _write(root, SCHEMA_CODE, b'SCHEMA_VERSION = "1.0.0"\n')


def _release_identity(root: Path, commit: str) -> dict[str, object]:
    with patch("tools.release.offline_version_inventory._verify_checkout_commit"):
        return release_train_identity(root, commit)


class OfflineVersionInventoryTests(unittest.TestCase):
    def test_current_repository_source_inventory(self) -> None:
        result = inventory(ROOT)
        self.assertEqual(result["studio_version"], "0.1.0")
        self.assertEqual(result["capture_version"], "0.1.0")
        self.assertEqual(result["capture_build"], 1)
        self.assertEqual(result["packscan_schema_version"], "1.0.0")
        self.assertEqual(result["status"], "OFFLINE_UNVERIFIED_BUILD")
        self.assertIsNone(result["artifact_sha256"])
        self.assertFalse(result["hosted_build_verified"])
        self.assertEqual(result["factory_release"], "NOT_AUTHORIZED")

    def test_synthetic_fixture_versions_are_independent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_fixture(root)
            self.assertEqual(inventory(root)["capture_bundle_id"], "com.packlab.capture")
            _write(root, SCHEMA, b'{"properties":{"schema_version":{"const":"2.0.0"}}}')
            _write(root, SCHEMA_CODE, b'SCHEMA_VERSION = "2.0.0"\n')
            self.assertEqual(inventory(root)["packscan_schema_version"], "2.0.0")

    def test_schema_contract_and_core_version_must_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_fixture(root)
            _write(root, SCHEMA_CODE, b'SCHEMA_VERSION = "1.1.0"\n')
            with self.assertRaisesRegex(SourceVersionError, "PACKSCAN_SCHEMA_VERSION_MISMATCH"):
                inventory(root)

    def test_release_train_binds_independent_versions_and_exact_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_fixture(root)
            studio_version = "0.8.4-rc.1+windows.7"
            capture_version = "1.2.3-beta.2+ios.11"
            _write(
                root,
                "pyproject.toml",
                f'[project]\nname = "packlab"\nversion = "{studio_version}"\n'.encode(),
            )
            _write(root, STUDIO, f'__version__ = "{studio_version}"\n'.encode())
            _write(root, APP, _project(capture_version, capture_version).encode())
            _write(root, SCHEMA, b'{"properties":{"schema_version":{"const":"2.0.0"}}}')
            _write(root, SCHEMA_CODE, b'SCHEMA_VERSION = "2.0.0"\n')
            commit = "0123456789abcdef0123456789abcdef01234567"

            first = _release_identity(root, commit)
            second = _release_identity(root, commit)

            self.assertEqual(first, second)
            self.assertEqual(first["source_commit"], commit)
            self.assertEqual(
                first["release_train"]["versions"],
                {
                    "studio": studio_version,
                    "capture": capture_version,
                    "capture_build": 1,
                    "packscan_schema": "2.0.0",
                },
            )
            self.assertEqual(
                first["release_train"]["id"],
                "packlab-rt-v1-" + first["release_train"]["identity_sha256"],
            )
            self.assertNotEqual(
                first["release_train"]["id"],
                _release_identity(root, "1123456789abcdef0123456789abcdef01234567")[
                    "release_train"
                ]["id"],
            )
            _write(root, SCHEMA_CODE, b'SCHEMA_VERSION = "2.1.0"\n')
            _write(root, SCHEMA, b'{"properties":{"schema_version":{"const":"2.1.0"}}}')
            self.assertNotEqual(
                first["release_train"]["id"],
                _release_identity(root, commit)["release_train"]["id"],
            )

    def test_release_train_rejects_invalid_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_fixture(root)
            for commit in ("", "0" * 39, "0" * 40 + "0", "g" * 40, "A" * 40):
                with self.subTest(commit=commit):
                    with self.assertRaisesRegex(SourceVersionError, "INVALID_SOURCE_COMMIT"):
                        release_train_identity(root, commit)

    def test_checkout_commit_mismatch_and_dirty_sources_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_fixture(root)
            _git(root, "init", "--quiet")
            _git(root, "config", "user.email", "packlab-test@example.invalid")
            _git(root, "config", "user.name", "PackLab Test")
            _git(root, "add", "--", ".")
            _git(root, "commit", "--quiet", "-m", "synthetic version fixture")
            commit = _git(root, "rev-parse", "HEAD")

            self.assertEqual(release_train_identity(root, commit)["source_commit"], commit)
            with self.assertRaisesRegex(SourceVersionError, "SOURCE_COMMIT_MISMATCH"):
                _verify_checkout_commit(root, "1123456789abcdef0123456789abcdef01234567")

            (root / SCHEMA_CODE).write_text('SCHEMA_VERSION = "1.1.0"\n', encoding="utf-8")
            _git(root, "update-index", "--assume-unchanged", SCHEMA_CODE)
            with self.assertRaisesRegex(SourceVersionError, "SOURCE_VERSION_TREE_MISMATCH"):
                release_train_identity(root, commit)

    def test_linked_version_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_fixture(root)
            schema = root / SCHEMA
            target = root / "schema-target.json"
            target.write_bytes(schema.read_bytes())
            schema.unlink()
            try:
                schema.symlink_to(target)
            except OSError:
                self.skipTest("symlink creation is unavailable in this environment")
            with self.assertRaisesRegex(SourceVersionError, "LINKED_VERSION_SOURCE_REJECTED"):
                inventory(root)

    def test_junction_version_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_fixture(root)
            path_type = type(root)
            original_is_junction = path_type.is_junction

            def is_test_junction(path: Path) -> bool:
                return path.name == "schemas" or original_is_junction(path)

            with patch.object(path_type, "is_junction", new=is_test_junction):
                with self.assertRaisesRegex(SourceVersionError, "LINKED_VERSION_SOURCE_REJECTED"):
                    inventory(root)

    def test_studio_version_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_fixture(root)
            _write(root, STUDIO, b'__version__ = "0.2.0"\n')
            with self.assertRaisesRegex(SourceVersionError, "STUDIO_VERSION_MISMATCH"):
                inventory(root)

    def test_debug_release_capture_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_fixture(root)
            _write(root, APP, _project("0.1.0", "0.2.0").encode())
            with self.assertRaisesRegex(SourceVersionError, "INCONSISTENT_CAPTURE_CONFIGS"):
                inventory(root)

    def test_invalid_schema_and_missing_sources_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_fixture(root)
            _write(root, SCHEMA, b'{"properties":{"schema_version":{"const":"1.0"}}}')
            with self.assertRaisesRegex(SourceVersionError, "INVALID_SEMVER"):
                inventory(root)
            (root / SCHEMA).unlink()
            with self.assertRaisesRegex(SourceVersionError, "REQUIRED_SOURCE_UNAVAILABLE"):
                inventory(root)

    def test_invalid_semver_and_duplicate_schema_keys_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_fixture(root)
            _write(root, SCHEMA, b'{"properties":{"schema_version":{"const":"1.0.0-01"}}}')
            with self.assertRaisesRegex(SourceVersionError, "INVALID_SEMVER"):
                inventory(root)
            _write(
                root,
                SCHEMA,
                b'{"properties":{"schema_version":{"const":"1.0.0"}},'
                b'"properties":{"schema_version":{"const":"2.0.0"}}}',
            )
            with self.assertRaisesRegex(SourceVersionError, "AMBIGUOUS_SCHEMA_VERSION_SOURCE"):
                inventory(root)

    def test_dotted_prerelease_and_build_identifiers_are_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_fixture(root)
            version = "1.2.3-rc.1+build.42"
            _write(
                root,
                "pyproject.toml",
                f'[project]\nname = "packlab"\nversion = "{version}"\n'.encode(),
            )
            _write(root, STUDIO, f'__version__ = "{version}"\n'.encode())
            _write(root, APP, _project(version, version).encode("utf-8"))
            result = inventory(root)
            self.assertEqual(result["studio_version"], version)
            self.assertEqual(result["capture_version"], version)

    def test_semver_rejects_invalid_prerelease_identifiers(self) -> None:
        invalid_versions = (
            "1.2.3-rc.",
            "1.2.3-.rc",
            "1.2.3-rc..1",
            "1.2.3-rc.01",
            "1.2.3-rc.١",
            "1.2.3-rc_1",
        )
        for version in invalid_versions:
            with self.subTest(version=version), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                _make_fixture(root)
                _write(root, STUDIO, f'__version__ = "{version}"\n'.encode())
                with self.assertRaisesRegex(SourceVersionError, "INVALID_SEMVER"):
                    inventory(root)

    def test_info_plist_substitution_must_remain_source_bound(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_fixture(root)
            _write(root, INFO, plistlib.dumps({"CFBundleVersion": "1"}))
            with self.assertRaisesRegex(
                SourceVersionError, "CAPTURE_PLIST_VERSION_BINDING_MISMATCH"
            ):
                inventory(root)


if __name__ == "__main__":
    unittest.main()
