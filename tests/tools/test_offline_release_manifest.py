"""Synthetic contract checks for offline candidate-description validation."""

from __future__ import annotations

import copy
import unittest

from tools.release.offline_release_manifest import validate_candidate

SOURCE_SHA = "a" * 40
ARTIFACT_SHA = "b" * 64
SIGNATURE_SHA = "c" * 64


def _candidate() -> dict[str, object]:
    return {
        "source": {"sha": SOURCE_SHA},
        "versions": {
            "studio": "0.1.0", "capture": "0.1.0", "capture_build": 1,
            "packscan_schema": "1.0.0",
        },
        "packscan_compatibility": {"read": ["1.0.0"], "write": "1.0.0"},
        "artifacts": [{
            "name": "capture-app", "sha256": ARTIFACT_SHA,
            "source_sha": SOURCE_SHA, "provenance_id": "synthetic provenance",
        }],
        "license_notices": [{
            "artifact_name": "capture-app", "license_id": "Example-License",
            "notice_ref": "docs/example-notice.md",
        }],
        "acceptance": {
            "pl0354_full_xctest": "AUDITED_PASS", "m17": "AUDITED_PASS",
            "independent_audits": [{
                "id": "SYNTHETIC-TEST-AUDIT", "status": "AUDITED_PASS",
                "audit_ref": "synthetic/audit.md",
            }],
        },
        "signed_release": False,
        "signatures": [],
    }


class OfflineReleaseManifestTests(unittest.TestCase):
    def test_complete_synthetic_description_is_not_release_authorization(self) -> None:
        result = validate_candidate(_candidate())
        self.assertEqual(result["status"], "PREPARATION_INPUT_COMPLETE_NOT_RELEASE_AUTHORIZATION")
        self.assertEqual(result["errors"], [])

    def test_missing_fields_and_actual_source_identity_fail_closed(self) -> None:
        data = _candidate()
        del data["license_notices"]
        self.assertEqual(validate_candidate(data)["status"], "BLOCKED")
        data = _candidate()
        data["source"] = {"sha": "not-a-commit"}
        self.assertIn("SOURCE_SHA_MISSING_OR_INVALID", validate_candidate(data)["errors"])

    def test_unaccepted_pl0354_and_m17_gates_block(self) -> None:
        data = _candidate()
        data["acceptance"]["pl0354_full_xctest"] = "BLOCKED_NOT_RUN"
        data["acceptance"]["m17"] = "NOT_ACCEPTED"
        errors = validate_candidate(data)["errors"]
        self.assertIn("PL0354_FULL_XCTEST_NOT_ACCEPTED", errors)
        self.assertIn("M17_NOT_ACCEPTED", errors)

    def test_artifact_provenance_digest_and_notice_must_bind(self) -> None:
        data = _candidate()
        data["artifacts"][0]["source_sha"] = "d" * 40
        data["artifacts"][0]["sha256"] = "not-a-digest"
        data["license_notices"] = []
        errors = validate_candidate(data)["errors"]
        self.assertIn("ARTIFACT_SOURCE_MISMATCH", errors)
        self.assertIn("ARTIFACT_DIGEST_MISSING_OR_INVALID", errors)
        self.assertIn("ARTIFACT_LICENSE_NOTICE_MISSING", errors)

    def test_signed_description_requires_signature_per_artifact(self) -> None:
        data = _candidate()
        data["signed_release"] = True
        self.assertIn("SIGNED_ARTIFACT_SIGNATURE_MISSING", validate_candidate(data)["errors"])
        data["signatures"] = [{
            "artifact_sha256": ARTIFACT_SHA, "signature_sha256": SIGNATURE_SHA,
            "identity_ref": "synthetic-signing-identity",
        }]
        self.assertNotIn("SIGNED_ARTIFACT_SIGNATURE_MISSING", validate_candidate(data)["errors"])

    def test_unknown_fields_and_schema_support_inconsistency_block(self) -> None:
        data = _candidate()
        data["packscan_compatibility"]["guess_future"] = True
        self.assertIn("PACKSCAN_SUPPORT_MISSING_OR_UNEXPECTED", validate_candidate(data)["errors"])
        data = copy.deepcopy(_candidate())
        data["artifacts"][0]["unreviewed"] = "value"
        self.assertIn("ARTIFACT_FIELDS_MISSING_OR_UNEXPECTED", validate_candidate(data)["errors"])


if __name__ == "__main__":
    unittest.main()
