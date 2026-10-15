"""Offline, stdlib-only checks; no CI or package installation needed."""

from __future__ import annotations

import json
import plistlib
import tempfile
import unittest
from pathlib import Path

from tools.release.offline_version_inventory import SourceVersionError, inventory

ROOT = Path(__file__).resolve().parents[2]
APP = "apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj"
INFO = "apps/ios-capture/PackLabCapture/Info.plist"
STUDIO = "apps/windows-studio/src/packlab_studio/__init__.py"
SCHEMA = "schemas/packscan/manifest.schema.json"


def _write(root: Path, rel: str, content: bytes) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


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
            self.assertEqual(inventory(root)["packscan_schema_version"], "2.0.0")

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

    def test_info_plist_substitution_must_remain_source_bound(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_fixture(root)
            _write(root, INFO, plistlib.dumps({"CFBundleVersion": "1"}))
            with self.assertRaisesRegex(SourceVersionError, "CAPTURE_PLIST_VERSION_BINDING_MISMATCH"):
                inventory(root)


if __name__ == "__main__":
    unittest.main()
