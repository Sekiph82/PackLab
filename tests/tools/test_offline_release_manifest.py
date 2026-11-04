"""Positive, negative, determinism, and boundary tests for release manifests."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from tools.release.offline_release_manifest import (
    _BUILD_SOURCE_FILES,
    _committed_source,
    _verify_build_sources,
    generate_manifest,
)
from tools.release.offline_version_inventory import release_train_identity

ROOT = Path(__file__).resolve().parents[2]


def _write_json(path: Path, value: Any) -> dict[str, str]:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    path.write_bytes(encoded)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


class OfflineReleaseManifestTests(unittest.TestCase):
    def _candidate(self, directory: Path) -> dict[str, Any]:
        commit = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        source = release_train_identity(ROOT, commit)
        package_digest = hashlib.sha256(
            _committed_source(ROOT, commit, _BUILD_SOURCE_FILES[2])
        ).hexdigest()
        versions = {
            "studio": source["studio_version"],
            "capture": source["capture_version"],
            "capture_build": source["capture_build"],
            "packscan_schema": source["packscan_schema_version"],
        }
        records = []
        for platform, name, digest, kind in (
            ("windows", "packlab-installer", "a" * 64, "windows_installer"),
            ("ios", "capture-simulator", "b" * 64, "ios_simulator_app"),
        ):
            receipt = {
                "platform": platform,
                "artifact_name": name,
                "artifact_kind": kind,
                "artifact_sha256": digest,
                "artifact_bytes": 1234,
                "source_commit": commit,
                "workflow_run_id": "41774735668",
                "signing_state": "UNSIGNED",
            }
            if platform == "ios":
                receipt["package_resolved_sha256"] = package_digest
            ref = _write_json(directory / f"{platform}-provenance.json", receipt)
            records.append({"platform": platform, "provenance_ref": ref})

        windows = {
            "source_commit": commit,
            "workflow_run_id": "41774735668",
            "artifact_sha256s": ["a" * 64],
            "python": "3.12.10",
            "qt": "6.11.2",
            "ocp": "7.9.3.1.1",
            "occt": "7.9.3",
            "open3d": "0.20.0",
        }
        ios = {
            "source_commit": commit,
            "workflow_run_id": "41774735668",
            "artifact_sha256s": ["b" * 64],
            "package_resolved_sha256": package_digest,
            "xcode_version": "16.0",
            "xcode_build": "16A242d",
            "sdk": "18.0",
            "swift_language_mode": "6.0",
            "swift_compiler": "6.0.3",
            "nextlevel_version": "0.19.1",
            "nextlevel_revision": "edb3ba52aed8b49e9e197a275ea5e4846fb8c36d",
        }
        windows_ref = _write_json(directory / "windows-build.json", windows)
        ios_ref = _write_json(directory / "ios-build.json", ios)
        return {
            "source_commit": commit,
            "release_train_id": source["release_train"]["id"],
            "versions": versions,
            "artifacts": records,
            "windows_build_identity": {"evidence_ref": windows_ref},
            "ios_build_identity": {"evidence_ref": ios_ref},
            "packscan_compatibility": {
                "read_min": "1.0.0",
                "read_max": "1.0.0",
                "write": "1.0.0",
                "migrations": [],
                "evidence_ref": {
                    "path": "docs/packscan/container-layout.md",
                    "sha256": hashlib.sha256(
                        (ROOT / "docs/packscan/container-layout.md").read_bytes()
                    ).hexdigest(),
                },
            },
            "third_party_notice_inventory": {
                "path": "docs/architecture/DEPENDENCY_LICENSE_REGISTER.md",
                "sha256": hashlib.sha256(
                    (ROOT / "docs/architecture/DEPENDENCY_LICENSE_REGISTER.md").read_bytes()
                ).hexdigest(),
            },
            "known_limitations": [
                "legal_review_pending",
                "m17_not_accepted",
                "physical_device_acceptance_pending",
            ],
        }

    def test_complete_evidence_generates_preparation_only_manifest(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="release-fixture-", dir=ROOT / "docs" / "packaging"
        ) as temp:
            result = generate_manifest(self._candidate(Path(temp)), ROOT)
        self.assertEqual(result["status"], "PREPARATION_ONLY_NOT_RELEASE_AUTHORIZATION")
        self.assertEqual(result["release_authorization"], "NOT_GRANTED")
        self.assertEqual(result["m17_status"], "NOT_ACCEPTED")
        self.assertEqual(
            {artifact["platform"] for artifact in result["artifacts"]}, {"windows", "ios"}
        )
        self.assertEqual(result["packscan_compatibility"]["migrations"], [])
        self.assertTrue(result["manifest_id"].startswith("packlab-rm-v1-"))
        schema = json.loads(
            (ROOT / "schemas/release/release-manifest.schema.json").read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(schema)
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(result)), [])

    def test_missing_reference_or_mismatched_content_digest_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="release-fixture-", dir=ROOT / "docs" / "packaging"
        ) as temp:
            candidate = self._candidate(Path(temp))
            del candidate["third_party_notice_inventory"]
            missing = generate_manifest(candidate, ROOT)
            self.assertEqual(missing["status"], "BLOCKED")
            candidate = self._candidate(Path(temp))
            candidate["artifacts"][0]["provenance_ref"]["sha256"] = "0" * 64
            mismatch = generate_manifest(candidate, ROOT)
        self.assertIn("EVIDENCE_DIGEST_MISMATCH", mismatch["errors"])

    def test_script_cli_rejects_incomplete_candidate_without_writing_manifest(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="release-cli-", dir=ROOT / "docs" / "packaging"
        ) as temp:
            directory = Path(temp)
            candidate_path = directory / "candidate.json"
            output_path = directory / "manifest.json"
            candidate_path.write_text("{}", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools/release/offline_release_manifest.py"),
                    str(candidate_path),
                    "--repo",
                    str(ROOT),
                    "--output",
                    str(output_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(
                json.loads(result.stdout),
                {"status": "BLOCKED", "errors": ["CANDIDATE_FIELDS_MISSING_OR_UNEXPECTED"]},
            )
            self.assertFalse(output_path.exists())

    def test_artifact_receipt_must_bind_source_platform_and_signing_state(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="release-fixture-", dir=ROOT / "docs" / "packaging"
        ) as temp:
            candidate = self._candidate(Path(temp))
            ref_path = ROOT / candidate["artifacts"][0]["provenance_ref"]["path"]
            receipt = json.loads(ref_path.read_text(encoding="utf-8"))
            receipt["source_commit"] = "d" * 40
            ref = _write_json(ref_path, receipt)
            candidate["artifacts"][0]["provenance_ref"] = ref
            receipt["signing_state"] = "UNSIGNED"
            receipt["signature_verification_ref"] = {
                "path": "tests/fixtures/release/missing-signature.json",
                "sha256": "c" * 64,
            }
            ref = _write_json(ref_path, receipt)
            candidate["artifacts"][0]["provenance_ref"] = ref
            result = generate_manifest(candidate, ROOT)
        self.assertIn("ARTIFACT_SOURCE_MISMATCH", result["errors"])
        self.assertIn("UNSIGNED_ARTIFACT_HAS_SIGNATURE_CLAIM", result["errors"])

    def test_artifact_kind_cannot_contradict_per_artifact_signing_state(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="release-fixture-", dir=ROOT / "docs" / "packaging"
        ) as temp:
            directory = Path(temp)
            for kind, signing in (
                ("ios_signed_ipa", "UNSIGNED"),
                ("ios_unsigned_device_archive", "SIGNED_VERIFIED"),
            ):
                candidate = self._candidate(directory)
                ios_record = candidate["artifacts"][1]
                receipt_path = ROOT / ios_record["provenance_ref"]["path"]
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                receipt["artifact_kind"] = kind
                receipt["signing_state"] = signing
                receipt.pop("signature_verification_ref", None)
                ios_record["provenance_ref"] = _write_json(receipt_path, receipt)
                result = generate_manifest(candidate, ROOT)
                self.assertIn("ARTIFACT_KIND_SIGNING_STATE_MISMATCH", result["errors"])

    def test_path_traversal_absolute_unc_and_linked_references_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="release-fixture-", dir=ROOT / "docs" / "packaging"
        ) as temp:
            for bad in (
                "../private.json",
                "C:/private.json",
                "\\\\server\\share\\x",
                "/private.json",
                "https://example.test/evidence",
                "docs/./private.json",
                "docs//private.json",
                "tests/private.json",
            ):
                candidate = self._candidate(Path(temp))
                candidate["artifacts"][0]["provenance_ref"]["path"] = bad
                self.assertIn(
                    "EVIDENCE_PATH_UNSAFE_OR_MISSING", generate_manifest(candidate, ROOT)["errors"]
                )

    def test_symlink_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="release-fixture-", dir=ROOT / "docs" / "packaging"
        ) as temp:
            directory = Path(temp)
            candidate = self._candidate(directory)
            target = directory / "windows-provenance.json"
            link = directory / "linked-provenance.json"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"symlink creation unavailable: {error}")
            candidate["artifacts"][0]["provenance_ref"]["path"] = link.relative_to(ROOT).as_posix()
            result = generate_manifest(candidate, ROOT)
        self.assertIn("EVIDENCE_PATH_UNSAFE_OR_MISSING", result["errors"])

    def test_verified_signature_receipt_is_per_artifact_and_digest_bound(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="release-fixture-", dir=ROOT / "docs" / "packaging"
        ) as temp:
            directory = Path(temp)
            candidate = self._candidate(directory)
            receipt_path = ROOT / candidate["artifacts"][0]["provenance_ref"]["path"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            signature_ref = _write_json(
                directory / "signature-check.json",
                {
                    "artifact_sha256": receipt["artifact_sha256"],
                    "signature_sha256": "c" * 64,
                    "verification_status": "SIGNATURE_VERIFIED",
                    "verification_tool": "codesign-verify-v1",
                },
            )
            receipt["signing_state"] = "SIGNED_VERIFIED"
            receipt["signature_verification_ref"] = signature_ref
            candidate["artifacts"][0]["provenance_ref"] = _write_json(receipt_path, receipt)
            valid = generate_manifest(candidate, ROOT)
            signature_ref["sha256"] = "d" * 64
            receipt["signature_verification_ref"] = signature_ref
            candidate["artifacts"][0]["provenance_ref"] = _write_json(receipt_path, receipt)
            invalid = generate_manifest(candidate, ROOT)
        signed = [
            artifact
            for artifact in valid["artifacts"]
            if artifact["signing_state"] == "SIGNED_VERIFIED"
        ]
        self.assertEqual(len(signed), 1)
        self.assertEqual(signed[0]["platform"], "windows")
        self.assertIn("EVIDENCE_DIGEST_MISMATCH", invalid["errors"])

    def test_advertising_an_m17_pass_is_not_an_accepted_candidate_shape(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="release-fixture-", dir=ROOT / "docs" / "packaging"
        ) as temp:
            candidate = self._candidate(Path(temp))
            candidate["m17_status"] = "AUDITED_PASS"
            result = generate_manifest(candidate, ROOT)
        self.assertEqual(result["errors"], ["CANDIDATE_FIELDS_MISSING_OR_UNEXPECTED"])

    def test_dependency_and_toolchain_sources_are_bound_to_head_even_assume_unchanged(self) -> None:
        for target_relative in (_BUILD_SOURCE_FILES[2], _BUILD_SOURCE_FILES[-1]):
            with tempfile.TemporaryDirectory(prefix="release-source-binding-") as temp:
                repository = Path(temp)
                subprocess.run(["git", "init", "--quiet", str(repository)], check=True)
                for index, relative in enumerate(_BUILD_SOURCE_FILES):
                    source = repository / relative
                    source.parent.mkdir(parents=True, exist_ok=True)
                    source.write_text(f"fixture source {index}\n", encoding="utf-8")
                subprocess.run(
                    ["git", "-C", str(repository), "add", "--", *list(_BUILD_SOURCE_FILES)],
                    check=True,
                )
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(repository),
                        "-c",
                        "user.name=PackLab Test",
                        "-c",
                        "user.email=packlab-test@example.invalid",
                        "commit",
                        "--quiet",
                        "-m",
                        "fixture",
                    ],
                    check=True,
                )
                commit = subprocess.run(
                    ["git", "-C", str(repository), "rev-parse", "HEAD"],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                _verify_build_sources(repository, commit)
                target = repository / target_relative
                target.write_text("modified dependency/toolchain source\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "BUILD_SOURCE_TREE_MISMATCH"):
                    _verify_build_sources(repository, commit)
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(repository),
                        "update-index",
                        "--assume-unchanged",
                        target_relative,
                    ],
                    check=True,
                )
                with self.assertRaisesRegex(ValueError, "BUILD_SOURCE_TREE_MISMATCH"):
                    _verify_build_sources(repository, commit)

    def test_manifest_identity_is_order_and_reference_path_independent(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="release-fixture-a-", dir=ROOT / "docs" / "packaging"
        ) as first:
            first_candidate = self._candidate(Path(first))
            result_a = generate_manifest(first_candidate, ROOT)
        with tempfile.TemporaryDirectory(
            prefix="release-fixture-b-", dir=ROOT / "docs" / "packaging"
        ) as second:
            second_candidate = self._candidate(Path(second))
            second_candidate["artifacts"].reverse()
            result_b = generate_manifest(second_candidate, ROOT)
        self.assertEqual(result_a["manifest_id"], result_b["manifest_id"])
        self.assertNotEqual(
            result_a["artifacts"][0]["provenance_ref"], result_b["artifacts"][0]["provenance_ref"]
        )

    def test_source_versions_compatibility_toolchain_and_m17_are_not_caller_overridable(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="release-fixture-", dir=ROOT / "docs" / "packaging"
        ) as temp:
            candidate = self._candidate(Path(temp))
            candidate["versions"]["studio"] = "9.9.9"
            candidate["release_train_id"] = "packlab-rt-v1-" + "f" * 64
            candidate["packscan_compatibility"]["read_max"] = "1.1.0"
            candidate["ios_build_identity"]["evidence_ref"] = {
                **candidate["ios_build_identity"]["evidence_ref"]
            }
            ios_path = ROOT / candidate["ios_build_identity"]["evidence_ref"]["path"]
            ios = json.loads(ios_path.read_text(encoding="utf-8"))
            ios["swift_language_mode"] = "5.0"
            candidate["ios_build_identity"]["evidence_ref"] = _write_json(ios_path, ios)
            result = generate_manifest(candidate, ROOT)
        self.assertIn("SOURCE_VERSION_MISMATCH", result["errors"])
        self.assertIn("RELEASE_TRAIN_ID_MISMATCH", result["errors"])
        self.assertIn("PACKSCAN_COMPATIBILITY_UNSUPPORTED_CLAIM", result["errors"])
        self.assertIn("IOS_SWIFT_LANGUAGE_MODE_MISMATCH", result["errors"])

    def test_rollback_manifest_rejects_unimplemented_schema_migrations(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="release-fixture-", dir=ROOT / "docs" / "packaging"
        ) as temp:
            candidate = self._candidate(Path(temp))
            candidate["packscan_compatibility"]["migrations"] = [
                {"source_schema": "1.0.0", "target_schema": "0.9.0"}
            ]
            result = generate_manifest(candidate, ROOT)
        self.assertIn("PACKSCAN_MIGRATION_UNSUPPORTED_CLAIM", result["errors"])


if __name__ == "__main__":
    unittest.main()
