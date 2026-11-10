"""Synthetic canaries for redacted, local Apple signing source checks."""

from __future__ import annotations

import contextlib
import hashlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.ci import ci_data_safety
from tools.ci.ci_data_safety import (
    _load_signing_document_allowlist,
    _report,
    scan_signing_material,
)


class SigningMaterialSafetyTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows path aliases are case-insensitive")
    def test_windows_path_alias_uses_resolved_repository_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "signing.py"
            header = "-----BEGIN " + "PRIVATE KEY-----"
            source.write_text(header, encoding="utf-8")
            alias = Path(str(source).swapcase())
            self.assertEqual(
                [finding.code for finding in scan_signing_material(root, [alias])],
                ["PRIVATE_KEY_BLOCK_PRESENT"],
            )

    def test_allowlist_rejects_non_object_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "tools" / "ci" / "ci_signing_material_allowlist.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SIGNING_ALLOWLIST_SCHEMA_INVALID"):
                _load_signing_document_allowlist(root)

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
                f'APPLE_PRIVATE_KEY = "{canary}"\n'
                + header
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
            source.write_text(
                "APPLE_API_TOKEN = SYNTHETIC-CANARY-NOT-A-CREDENTIAL\n", encoding="utf-8"
            )
            self.assertEqual(
                [finding.code for finding in scan_signing_material(root, [source])],
                ["DIRECT_SECRET_ASSIGNMENT"],
            )

    def test_alphanumeric_token_shapes_are_not_mistaken_for_constant_names(self) -> None:
        # PL-0394 N1: values were upper-cased before the constant-name exemption, so any
        # letters/digits/underscore secret slipped through. Synthetic shapes only.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            leaking = (
                'APPLE_TEAM_ID = "Q7SYNTH3TC"',
                "APPLE_API_KEY_ID = K9SYNTH4XZ",
                'GITHUB_TOKEN = "ghp_SynthEticCanary0123456789abcdefABCD"',
                "API_TOKEN = glpatSynthEticCanary0123",
                'ACCESS_TOKEN = "AKIASYNTHETIC0CANARY"',
            )
            for index, line in enumerate(leaking):
                with self.subTest(line=line.split("=")[0]):
                    source = root / f"leak-{index}.py"
                    source.write_text(line + "\n", encoding="utf-8")
                    self.assertEqual(
                        [finding.code for finding in scan_signing_material(root, [source])],
                        ["DIRECT_SECRET_ASSIGNMENT"],
                    )
            references = (
                'APPLE_API_TOKEN = "APPLE_API_TOKEN_ENV_NAME"',
                "GITHUB_TOKEN = settings.github_token",
                "API_TOKEN = api_token",
            )
            for index, line in enumerate(references):
                with self.subTest(reference=line):
                    source = root / f"ref-{index}.py"
                    source.write_text(line + "\n", encoding="utf-8")
                    self.assertEqual(scan_signing_material(root, [source]), [])

    def test_common_signing_exports_are_detected_without_echoing_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canary = "SYNTHETIC-CANARY-NOT-A-CREDENTIAL"
            names = (
                "export APPLE_SIGNING_CERTIFICATE_P12_BASE64",
                "APPLE_CERTIFICATE_BASE64",
                "APPLE_SIGNING_CERTIFICATE_BASE64",
                "APPLE_PROVISIONING_PROFILE_BASE64",
                "MATCH_PASSWORD",
                "KEYCHAIN_PASSWORD",
            )
            for index, name in enumerate(names):
                with self.subTest(name=name):
                    source = root / f"settings-{index}.sh"
                    source.write_text(f'{name}="{canary}"\n', encoding="utf-8")
                    findings = scan_signing_material(root, [source])
                    self.assertEqual(
                        [finding.code for finding in findings],
                        ["DIRECT_SECRET_ASSIGNMENT"],
                    )
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        _report(findings)
                    self.assertNotIn(canary, output.getvalue())

    def test_document_marker_allowlist_requires_exact_reviewed_path_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = root / "docs" / "security" / "fixtures" / "marker.md"
            fixture.parent.mkdir(parents=True)
            header = b"-----BEGIN " + b"PRIVATE KEY-----"
            contents = b"Example marker: " + header + b" in prose; no key bytes present.\r\n"
            fixture.write_bytes(contents)
            canonical_digest = hashlib.sha256(contents.replace(b"\r\n", b"\n")).hexdigest()
            approved = {
                "docs/security/fixtures/marker.md": {
                    "sha256": canonical_digest,
                    "reason": "Reviewed documentation marker only; contains no key bytes.",
                }
            }
            with patch.dict(
                ci_data_safety.REVIEWED_SIGNING_MARKER_DOCUMENTS,
                {"docs/security/fixtures/marker.md": canonical_digest},
                clear=True,
            ):
                self.assertEqual(scan_signing_material(root, [fixture], approved), [])

                changed = contents + b"changed"
                fixture.write_bytes(changed)
                self.assertEqual(
                    [finding.code for finding in scan_signing_material(root, [fixture], approved)],
                    ["PRIVATE_KEY_BLOCK_PRESENT"],
                )

    def test_document_allowlist_never_suppresses_a_complete_private_key_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = root / "docs" / "security" / "fixtures" / "marker.md"
            fixture.parent.mkdir(parents=True)
            header = "-----BEGIN " + "PRIVATE KEY-----"
            footer = "-----END " + "PRIVATE KEY-----"
            contents = (
                "Example marker:\n" + header + "\n"
                "SYNTHETIC-KEY-CANARY-NOT-A-CREDENTIAL\n" + footer + "\n"
            ).encode()
            fixture.write_bytes(contents)
            approved = {
                "docs/security/fixtures/marker.md": {
                    "sha256": hashlib.sha256(contents).hexdigest(),
                    "reason": "Synthetic negative test; complete key block must remain blocked.",
                }
            }
            with patch.dict(
                ci_data_safety.REVIEWED_SIGNING_MARKER_DOCUMENTS,
                {
                    "docs/security/fixtures/marker.md": approved[
                        "docs/security/fixtures/marker.md"
                    ]["sha256"]
                },
                clear=True,
            ):
                self.assertEqual(
                    [finding.code for finding in scan_signing_material(root, [fixture], approved)],
                    ["PRIVATE_KEY_BLOCK_PRESENT"],
                )

    def test_document_allowlist_rejects_inline_base64_after_a_private_key_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = root / "docs" / "security" / "fixtures" / "marker.md"
            fixture.parent.mkdir(parents=True)
            header = "-----BEGIN " + "PRIVATE KEY-----"
            contents = ("Example marker: " + header + " " + "A" * 48 + "; end.\n").encode()
            fixture.write_bytes(contents)
            approved = {
                "docs/security/fixtures/marker.md": {
                    "sha256": hashlib.sha256(contents).hexdigest(),
                    "reason": "Synthetic negative test; inline payload must remain blocked.",
                }
            }
            with patch.dict(
                ci_data_safety.REVIEWED_SIGNING_MARKER_DOCUMENTS,
                {
                    "docs/security/fixtures/marker.md": approved[
                        "docs/security/fixtures/marker.md"
                    ]["sha256"]
                },
                clear=True,
            ):
                self.assertEqual(
                    [finding.code for finding in scan_signing_material(root, [fixture], approved)],
                    ["PRIVATE_KEY_BLOCK_PRESENT"],
                )

    def test_document_allowlist_cannot_cover_a_non_document_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = root / "assets" / "marker.md"
            fixture.parent.mkdir(parents=True)
            header = b"-----BEGIN " + b"PRIVATE KEY-----"
            contents = b"Example marker: " + header + b"\n"
            fixture.write_bytes(contents)
            allowlist = {
                "assets/marker.md": {
                    "sha256": hashlib.sha256(contents).hexdigest(),
                    "reason": "Must not broaden the documentation exception.",
                }
            }
            self.assertEqual(
                [finding.code for finding in scan_signing_material(root, [fixture], allowlist)],
                ["PRIVATE_KEY_BLOCK_PRESENT"],
            )

    def test_private_container_filename_is_reported_by_code_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private_file = root / "synthetic-signing-key.p12"
            private_file.write_bytes(b"synthetic empty canary")
            findings = scan_signing_material(root, [private_file])
            self.assertEqual(
                [finding.code for finding in findings], ["APPLE_SIGNING_MATERIAL_FILENAME"]
            )

    def test_certificate_profile_and_keychain_extensions_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            protected_paths = [
                root / "certificate.cer",
                root / "auth-key.p8",
                root / "login.keychain",
                root / "login.keychain-db",
            ]
            for path in protected_paths:
                path.write_bytes(b"synthetic empty canary")
            self.assertEqual(
                [finding.code for finding in scan_signing_material(root, protected_paths)],
                ["APPLE_SIGNING_MATERIAL_FILENAME"] * len(protected_paths),
            )

    def test_case_insensitive_pem_and_key_extensions_scan_private_key_headers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pem = root / "reviewed.PEM"
            key = root / "opaque.Key"
            header = "-----BEGIN " + "PRIVATE KEY-----"
            pem.write_text(header, encoding="utf-8")
            encrypted_header = "-----BEGIN ENCRYPTED " + "PRIVATE KEY-----"
            key.write_text(encrypted_header, encoding="utf-8")

            findings = scan_signing_material(root, [pem, key])
            self.assertEqual(
                [finding.code for finding in findings],
                ["PRIVATE_KEY_BLOCK_PRESENT", "PRIVATE_KEY_BLOCK_PRESENT"],
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(_report(findings), 1)
            self.assertNotIn(str(pem), output.getvalue())
            self.assertNotIn(str(key), output.getvalue())
            self.assertNotIn(header, output.getvalue())
            self.assertNotIn(encrypted_header, output.getvalue())

    def test_public_pem_certificate_is_not_treated_as_a_private_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            certificate = root / "public.PEM"
            certificate.write_text(
                "-----BEGIN CERTIFICATE-----\nSYNTHETIC_PUBLIC_CERTIFICATE\n"
                "-----END CERTIFICATE-----\n",
                encoding="utf-8",
            )
            self.assertEqual(scan_signing_material(root, [certificate]), [])

    def test_undecodable_pem_or_key_payload_fails_closed_without_echoing_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            protected = root / "opaque.key"
            protected.write_bytes(b"\xff\xfeSYNTHETIC_BINARY_CANARY")

            findings = scan_signing_material(root, [protected])
            self.assertEqual([finding.code for finding in findings], ["SIGNING_SCAN_UNREADABLE"])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(_report(findings), 1)
            self.assertNotIn(str(protected), output.getvalue())
            self.assertNotIn("SYNTHETIC_BINARY_CANARY", output.getvalue())


if __name__ == "__main__":
    unittest.main()
