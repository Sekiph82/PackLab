"""Synthetic canaries for redacted, local Apple signing source checks."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from tools.ci.ci_data_safety import _report, scan_signing_material


class SigningMaterialSafetyTests(unittest.TestCase):
    def test_safe_example_placeholder_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "safe.py"
            source.write_text('APPLE_PRIVATE_KEY = "<APPLE_KEY_EXAMPLE_ONLY>"\n', encoding="utf-8")
            self.assertEqual(scan_signing_material(root, [source]), [])

    def test_synthetic_private_key_canary_is_reported_without_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "signing.py"
            canary = "SYNTHETIC-CANARY-NOT-A-CREDENTIAL"
            header = "-----BEGIN " + "PRIVATE KEY-----"
            source.write_text(
                f'APPLE_PRIVATE_KEY = "{canary}"\n' + header
                + "\nSYNTHETIC_TEST_BODY_NOT_KEY_MATERIAL\n",
                encoding="utf-8",
            )
            findings = scan_signing_material(root, [source])
            self.assertEqual([finding.code for finding in findings], ["PRIVATE_KEY_BLOCK_PRESENT"])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(_report(findings), 1)
            self.assertNotIn(canary, output.getvalue())
            self.assertNotIn(str(source), output.getvalue())

    def test_direct_secret_assignment_uses_only_redacted_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "settings.py"
            canary = "SYNTHETIC-CANARY-NOT-A-CREDENTIAL"
            source.write_text(f'APPLE_API_TOKEN = "{canary}"\n', encoding="utf-8")
            findings = scan_signing_material(root, [source])
            self.assertEqual([finding.code for finding in findings], ["DIRECT_SECRET_ASSIGNMENT"])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                _report(findings)
            self.assertNotIn(canary, output.getvalue())

    def test_unquoted_direct_secret_assignment_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "settings.py"
            source.write_text("APPLE_API_TOKEN = SYNTHETIC-CANARY-NOT-A-CREDENTIAL\n", encoding="utf-8")
            self.assertEqual(
                [finding.code for finding in scan_signing_material(root, [source])],
                ["DIRECT_SECRET_ASSIGNMENT"],
            )

    def test_private_container_filename_is_reported_by_code_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private_file = root / "synthetic-signing-key.p12"
            private_file.write_bytes(b"synthetic empty canary")
            findings = scan_signing_material(root, [private_file])
            self.assertEqual([finding.code for finding in findings], ["APPLE_SIGNING_MATERIAL_FILENAME"])


if __name__ == "__main__":
    unittest.main()
