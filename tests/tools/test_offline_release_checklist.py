"""Focused fail-closed tests for the offline release checklist validator."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools.release.offline_release_checklist import (
    _accepted_audit_text,
    _milestone_audit,
    _validate_evidence_fields,
    main,
    render_checklist,
)

SOURCE = "a" * 40
DIGEST = "b" * 64
GATES = (
    "windows_ci_build_package_smoke",
    "redistribution_notice_inventory",
    "ios_swift_simulator_tests",
    "ios_unsigned_device_archive",
    "secrets_scan",
    "windows_artifact_provenance",
    "ios_artifact_provenance",
)


class OfflineReleaseChecklistTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.session = self.root / "coordination/sessions/M16-C001"
        self.session.mkdir(parents=True)
        task_ids = [f"PL-{n:04d}" for n in range(4000, 4010)]
        (self.root / "TASKS.md").write_text(
            "\n".join(f"- [x] **{task}** Example task" for task in task_ids),
            encoding="utf-8",
        )
        for index, gate in enumerate((*GATES, "physical_validation")):
            task_id = task_ids[index]
            fields = (
                f"Artifact SHA-256: {DIGEST}\nArtifact bytes: 12\nWorkflow run ID: 12345\n"
                if gate in {"windows_artifact_provenance", "ios_artifact_provenance"}
                else ""
            )
            audit = (
                f"Task: {task_id}\nGate Coverage: {gate}\nSource commit: `{SOURCE}`\n"
                f"{fields}Decision: AUDITED_PASS\n"
            )
            (self.session / f"{task_id}_CHATGPT_AUDIT_V01.md").write_text(audit, encoding="utf-8")
        (self.session / "M17-C001_CHATGPT_AUDIT_V01.md").write_text(
            f"Milestone: M17\nSource commit: `{SOURCE}`\nDecision: AUDITED_PASS\n",
            encoding="utf-8",
        )
        self.candidate = self._candidate(task_ids)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _candidate(self, task_ids: list[str]) -> dict:
        gates = {}
        for index, gate in enumerate(GATES):
            evidence = {
                "audit_task_id": task_ids[index],
                "audit_ref": f"coordination/sessions/M16-C001/{task_ids[index]}_CHATGPT_AUDIT_V01.md",
                "source_commit": SOURCE,
                "result": "PASS",
            }
            if gate in {"windows_artifact_provenance", "ios_artifact_provenance"}:
                evidence.update(artifact_sha256=DIGEST, artifact_bytes=12, workflow_run_id="12345")
            gates[gate] = evidence
        self.physical = {
            "audit_task_id": task_ids[7],
            "audit_ref": f"coordination/sessions/M16-C001/{task_ids[7]}_CHATGPT_AUDIT_V01.md",
            "source_commit": SOURCE,
            "result": "PASS",
        }
        return {
            "source_commit": SOURCE,
            "release_train_id": "packlab-rt-v1-" + DIGEST,
            "versions": {
                "studio": "0.1.0",
                "capture": "0.1.0",
                "capture_build": "1",
                "packscan_schema": "1.0.0",
            },
            "release_intent": "INTERNAL_UNSIGNED",
            "gates": {**gates, "signed_ipa": None},
            "m17_acceptance": {
                "status": "ACCEPTED",
                "audit_ref": "coordination/sessions/M16-C001/M17-C001_CHATGPT_AUDIT_V01.md",
            },
            "legal_review": {
                "status": "PENDING",
                "approval_id": None,
                "approval_ref": None,
                "evidence_sha256": None,
            },
            "physical_validation": {"status": "ACCEPTED", "evidence": self.physical},
            "known_limitations": [
                "formal_legal_review_pending",
                "known_unsupported_device_scope",
            ],
        }

    def test_legal_gate_remains_pending_until_authenticated_approval_is_supported(self) -> None:
        result = _validate_evidence_fields(self.root, self.candidate)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("FORMAL_LEGAL_REVIEW_PENDING", result["errors"])
        output = render_checklist(result, self.candidate["release_train_id"])
        self.assertIn("Release authorization: `NOT_GRANTED`", output)

    def test_pending_external_gates_are_blocked_and_surfaced(self) -> None:
        self.candidate["m17_acceptance"] = {"status": "NOT_ACCEPTED", "audit_ref": None}
        self.candidate["legal_review"] = {
            "status": "PENDING",
            "approval_id": None,
            "approval_ref": None,
            "evidence_sha256": None,
        }
        self.candidate["physical_validation"] = {"status": "PENDING", "evidence": None}
        self.candidate["known_limitations"] = [
            "m17_acceptance_not_granted",
            "formal_legal_review_pending",
            "physical_validation_pending",
        ]
        result = _validate_evidence_fields(self.root, self.candidate)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("M17_ACCEPTANCE_REQUIRED_BEFORE_PL0368", result["errors"])
        output = render_checklist(result, self.candidate["release_train_id"])
        self.assertIn("formal_legal_review_pending", output)
        self.assertIn("physical_validation_pending", output)

    def test_stale_source_and_audit_scope_do_not_pass(self) -> None:
        self.candidate["gates"][GATES[0]]["source_commit"] = "c" * 40
        audit_path = self.session / "PL-4000_CHATGPT_AUDIT_V01.md"
        audit_path.write_text(
            audit_path.read_text(encoding="utf-8").replace(GATES[0], "another_gate"),
            encoding="utf-8",
        )
        result = _validate_evidence_fields(self.root, self.candidate)
        self.assertIn("WINDOWS_CI_BUILD_PACKAGE_SMOKE_SOURCE_COMMIT_STALE", result["errors"])
        self.assertIn("WINDOWS_CI_BUILD_PACKAGE_SMOKE_AUDIT_SCOPE_MISMATCH", result["errors"])

    def test_latest_rejected_audit_prevents_fallback_to_older_pass(self) -> None:
        (self.session / "PL-4000_CHATGPT_AUDIT_V02.md").write_text(
            f"Task: PL-4000\nGate Coverage: {GATES[0]}\nDecision: AUDITED_FAIL\n", encoding="utf-8"
        )
        result = _validate_evidence_fields(self.root, self.candidate)
        self.assertIn("WINDOWS_CI_BUILD_PACKAGE_SMOKE_AUDIT_MISSING_OR_STALE", result["errors"])

    def test_signed_ipa_is_conditional_on_distribution_intent(self) -> None:
        self.candidate["release_intent"] = "SIGNED_DISTRIBUTION"
        result = _validate_evidence_fields(self.root, self.candidate)
        self.assertIn("SIGNED_IPA_EVIDENCE_FIELDS_INVALID", result["errors"])
        output = render_checklist(result, self.candidate["release_train_id"])
        self.assertIn("Signed IPA: `BLOCKED`", output)
        self.assertNotIn("NOT_REQUIRED_UNSIGNED_INTERNAL", output)

    def test_self_asserted_legal_approval_is_rejected(self) -> None:
        self.candidate["legal_review"].update(
            status="OWNER_APPROVED",
            approval_id="LEGAL-OWNER-2026",
            approval_ref="docs/packaging/legal-approvals/approval.md",
            evidence_sha256=DIGEST,
        )
        result = _validate_evidence_fields(self.root, self.candidate)
        self.assertIn("LEGAL_REVIEW_STATUS_INVALID", result["errors"])

    def test_quoted_or_duplicate_decision_text_does_not_override_audit_result(self) -> None:
        audit = self.session / "PL-4000_CHATGPT_AUDIT_V01.md"
        base = audit.read_text(encoding="utf-8")
        audit.write_text(
            base + "Reviewer note: Decision: AUDITED_PASS\nDecision: AUDITED_FAIL\n",
            encoding="utf-8",
        )
        self.assertIsNone(_accepted_audit_text(audit, "PL-4000"))

    def test_json_schema_accepts_artifact_shape_and_rejects_extra_fields(self) -> None:
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema is not installed in this environment")
        schema = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "schemas/release/release-checklist-input.schema.json"
            ).read_text(encoding="utf-8")
        )
        jsonschema.validate(self.candidate, schema)
        with self.assertRaises(jsonschema.ValidationError):
            bad_candidate = json.loads(json.dumps(self.candidate))
            bad_candidate["gates"]["windows_artifact_provenance"]["unexpected"] = "value"
            jsonschema.validate(bad_candidate, schema)

    def test_cli_writes_blocked_checklist_exclusively_outside_repo(self) -> None:
        candidate_path = self.root / "candidate.json"
        candidate_path.write_text(json.dumps(self.candidate), encoding="utf-8")
        with TemporaryDirectory() as output_temp:
            output_path = Path(output_temp) / "checklist.md"
            train = {
                "release_train": {
                    "id": self.candidate["release_train_id"],
                    "versions": self.candidate["versions"],
                }
            }
            with (
                patch(
                    "tools.release.offline_release_checklist._clean_source_commit",
                    return_value=SOURCE,
                ),
                patch(
                    "tools.release.offline_release_checklist.release_train_identity",
                    return_value=train,
                ),
            ):
                args = [
                    str(candidate_path),
                    "--repo",
                    str(self.root),
                    "--output",
                    str(output_path),
                ]
                self.assertEqual(main(args), 2)
                original = output_path.read_text(encoding="utf-8")
                self.assertIn("Release authorization: `NOT_GRANTED`", original)
                self.assertIn("formal_legal_review_pending", original)
                self.assertEqual(main(args), 2)
            self.assertEqual(output_path.read_text(encoding="utf-8"), original)

    def test_cli_rejects_release_train_mismatch_without_output(self) -> None:
        candidate_path = self.root / "candidate.json"
        candidate_path.write_text(json.dumps(self.candidate), encoding="utf-8")
        with TemporaryDirectory() as output_temp:
            output_path = Path(output_temp) / "checklist.md"
            wrong_train = {
                "release_train": {
                    "id": "packlab-rt-v1-" + "c" * 64,
                    "versions": self.candidate["versions"],
                }
            }
            with (
                patch(
                    "tools.release.offline_release_checklist._clean_source_commit",
                    return_value=SOURCE,
                ),
                patch(
                    "tools.release.offline_release_checklist.release_train_identity",
                    return_value=wrong_train,
                ),
            ):
                result = main(
                    [
                        str(candidate_path),
                        "--repo",
                        str(self.root),
                        "--output",
                        str(output_path),
                    ]
                )
            self.assertEqual(result, 2)
            self.assertFalse(output_path.exists())

    def test_malformed_input_fails_closed_without_renderer_crash(self) -> None:
        result = _validate_evidence_fields(self.root, {"source_commit": []})
        self.assertEqual(result["errors"], ["CHECKLIST_CANDIDATE_FIELDS_INVALID"])
        rendered = render_checklist(result, "unknown")
        self.assertIn("Status: `BLOCKED`", rendered)
        self.assertIn("Studio: `UNKNOWN`", rendered)

    def test_final_pass_token_is_exact(self) -> None:
        audit = self.session / "PL-4000_CHATGPT_AUDIT_V01.md"
        audit.write_text("Task: PL-4000\nDecision: AUDITED_PASSENGER\n", encoding="utf-8")
        self.assertIsNone(_accepted_audit_text(audit, "PL-4000"))

    def test_m17_audit_must_be_latest_and_current_source_bound(self) -> None:
        ref = "coordination/sessions/M16-C001/M17-C001_CHATGPT_AUDIT_V01.md"
        self.assertTrue(_milestone_audit(self.root, ref, SOURCE))
        self.assertFalse(_milestone_audit(self.root, ref, "d" * 40))


if __name__ == "__main__":
    unittest.main()
