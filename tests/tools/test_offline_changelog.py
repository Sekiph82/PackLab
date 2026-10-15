"""Synthetic checks for source-bound offline changelog draft validation."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.release.offline_changelog import validate_entries

TASK = "PL-1234"
SUMMARY = "Synthetic capability was added."


def _fixture(root: Path) -> tuple[dict[str, str], Path]:
    (root / "coordination/sessions/sample").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "TASKS.md").write_text(f"- [x] **{TASK}** Accepted synthetic fixture\n", encoding="utf-8")
    audit = root / "coordination/sessions/sample/PL-1234_CHATGPT_AUDIT_V01.md"
    audit.write_text(f"{TASK}\n## VERDICT: AUDITED_PASS\n", encoding="utf-8")
    source = root / "src/change.md"
    source.write_text(SUMMARY + "\n", encoding="utf-8")
    return ({
        "task_id": TASK,
        "summary": SUMMARY,
        "audit_ref": "coordination/sessions/sample/PL-1234_CHATGPT_AUDIT_V01.md",
        "source_ref": "src/change.md",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }, source)


class OfflineChangelogTests(unittest.TestCase):
    def test_accepted_note_must_match_cited_source_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry, _ = _fixture(root)
            result = validate_entries(root, [entry])
            self.assertEqual(result["status"], "OFFLINE_CHANGELOG_INPUT_VALIDATION_ONLY")
            self.assertEqual(result["errors"], [])

    def test_unaccepted_id_duplicate_id_and_commit_message_fields_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry, _ = _fixture(root)
            entry["task_id"] = "PL-5678"
            errors = validate_entries(root, [entry, entry])["errors"]
            self.assertIn("CHANGELOG_TASK_NOT_ACCEPTED", errors)
            self.assertIn("CHANGELOG_TASK_ID_DUPLICATE", errors)
            entry["commit_message"] = "infer from this arbitrary message"
            self.assertIn("CHANGELOG_ENTRY_FIELDS_MISSING_OR_UNEXPECTED", validate_entries(root, [entry])["errors"])

    def test_arbitrary_summary_bad_digest_and_unaccepted_audit_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry, _ = _fixture(root)
            entry["summary"] = "Claim absent from reviewed source."
            entry["source_sha256"] = "0" * 64
            (root / entry["audit_ref"]).write_text(f"{TASK}\n## VERDICT: CHANGES_REQUIRED\n", encoding="utf-8")
            errors = validate_entries(root, [entry])["errors"]
            self.assertIn("CHANGELOG_SUMMARY_NOT_IN_SOURCE_FRAGMENT", errors)
            self.assertIn("CHANGELOG_SOURCE_DIGEST_MISMATCH", errors)
            self.assertIn("CHANGELOG_AUDIT_CITATION_UNACCEPTED", errors)

    def test_traversal_paths_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry, _ = _fixture(root)
            entry["source_ref"] = "../outside.txt"
            self.assertIn("CHANGELOG_SOURCE_FRAGMENT_UNAVAILABLE", validate_entries(root, [entry])["errors"])


if __name__ == "__main__":
    unittest.main()
