"""Synthetic checks for task-audited, source-bound changelog generation."""

from __future__ import annotations

import contextlib
import hashlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.release.offline_changelog import (
    _safe_note,
    _write_new_output,
    main,
    render_changelog,
    validate_entries,
)

TASK = "PL-1234"
SUMMARY = "Synthetic capability was added."
LIMITATION = "Synthetic capability remains offline-only."
_TRAIN = {
    "release_train": {
        "id": "packlab-rt-v1-" + "a" * 64,
        "versions": {
            "studio": "0.1.0",
            "capture": "0.1.0",
            "capture_build": 1,
            "packscan_schema": "1.0.0",
        },
    }
}


def _fixture(root: Path, *, accepted: bool = True) -> dict[str, object]:
    (root / "coordination/sessions/sample").mkdir(parents=True)
    source_dir = root / "docs/packaging/release-notes"
    source_dir.mkdir(parents=True)
    checked = "x" if accepted else " "
    (root / "TASKS.md").write_text(
        f"# M01 - Synthetic milestone\n- [{checked}] **{TASK}** Synthetic accepted task\n",
        encoding="utf-8",
    )
    audit = root / f"coordination/sessions/sample/{TASK}_CHATGPT_AUDIT_V01.md"
    audit.write_text(f"{TASK}\nDecision: **AUDITED_PASS**\n", encoding="utf-8")
    source = source_dir / f"{TASK}.md"
    source.write_text(
        f"Task-ID: {TASK}\nCategory: Added\n{SUMMARY}\n{LIMITATION}\n", encoding="utf-8"
    )
    return {
        "task_id": TASK,
        "category": "Added",
        "summary": SUMMARY,
        "known_limitations": [LIMITATION],
        "audit_ref": f"coordination/sessions/sample/{TASK}_CHATGPT_AUDIT_V01.md",
        "source_ref": f"docs/packaging/release-notes/{TASK}.md",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }


class OfflineChangelogTests(unittest.TestCase):
    def test_note_filter_rejects_nested_paths_and_links(self) -> None:
        for note in (
            "See docs/packaging/release-notes/PL-1234.md",
            "Visit coordination/sessions/M16-C001/PL-1234.md",
            "See private/scans/2026/example.jpg",
            "Read /etc/passwd before release.",
            "[private](private/scans/example.jpg)",
        ):
            with self.subTest(note=note):
                self.assertFalse(_safe_note(note))

    def test_accepted_note_requires_digest_bound_fragment_and_final_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = _fixture(root)
            result = validate_entries(root, [entry])
            self.assertEqual(result["status"], "CHANGELOG_INPUT_VALIDATION_PASS")
            self.assertEqual(result["errors"], [])
            self.assertEqual(result["entries"][0]["milestone"], "M01")  # type: ignore[index]

    def test_unknown_unaccepted_and_duplicate_task_ids_reject(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = _fixture(root)
            unknown = dict(entry, task_id="PL-5678")
            errors = validate_entries(root, [unknown, unknown])["errors"]
            self.assertIn("CHANGELOG_TASK_ID_UNKNOWN", errors)
            self.assertIn("CHANGELOG_TASK_ID_DUPLICATE", errors)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = _fixture(root, accepted=False)
            self.assertIn("CHANGELOG_TASK_NOT_ACCEPTED", validate_entries(root, [entry])["errors"])

    def test_commit_message_fields_invalid_categories_and_unreviewed_audit_reject(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = _fixture(root)
            entry["commit_message"] = "Infer release truth from this arbitrary message"
            self.assertIn(
                "CHANGELOG_ENTRY_FIELDS_MISSING_OR_UNEXPECTED",
                validate_entries(root, [entry])["errors"],
            )
            del entry["commit_message"]
            entry["category"] = "Builder logs"
            (root / entry["audit_ref"]).write_text(
                f"{TASK}\nDecision: **CHANGES_REQUIRED**\n", encoding="utf-8"
            )
            errors = validate_entries(root, [entry])["errors"]
            self.assertIn("CHANGELOG_CATEGORY_INVALID", errors)
            self.assertIn("CHANGELOG_AUDIT_CITATION_UNACCEPTED", errors)

    def test_latest_audit_must_pass_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = _fixture(root)
            (root / f"coordination/sessions/sample/{TASK}_CHATGPT_AUDIT_V02.md").write_text(
                f"{TASK}\nDecision: **CHANGES_REQUIRED**\n", encoding="utf-8"
            )
            self.assertIn(
                "CHANGELOG_AUDIT_CITATION_UNACCEPTED", validate_entries(root, [entry])["errors"]
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = _fixture(root)
            (root / entry["audit_ref"]).write_text(
                f"{TASK}\nDecision: **AUDITED_PASSENGER**\n", encoding="utf-8"
            )
            self.assertIn(
                "CHANGELOG_AUDIT_CITATION_UNACCEPTED", validate_entries(root, [entry])["errors"]
            )

    def test_fragment_must_be_bound_to_entry_task_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = _fixture(root)
            wrong = root / "docs/packaging/release-notes/PL-5678.md"
            wrong.write_text(
                f"Task-ID: PL-5678\nCategory: Added\n{SUMMARY}\n{LIMITATION}\n",
                encoding="utf-8",
            )
            entry["source_ref"] = "docs/packaging/release-notes/PL-5678.md"
            entry["source_sha256"] = hashlib.sha256(wrong.read_bytes()).hexdigest()
            self.assertIn(
                "CHANGELOG_SOURCE_TASK_ID_MISMATCH", validate_entries(root, [entry])["errors"]
            )

    def test_category_must_match_reviewed_fragment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = _fixture(root)
            entry["category"] = "Fixed"
            self.assertIn(
                "CHANGELOG_CATEGORY_SOURCE_MISMATCH", validate_entries(root, [entry])["errors"]
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = _fixture(root)
            source = root / entry["source_ref"]
            source.write_text(
                f"Task-ID: {TASK}\nCategory: Added\nCategory: Fixed\n{SUMMARY}\n{LIMITATION}\n",
                encoding="utf-8",
            )
            entry["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertIn(
                "CHANGELOG_CATEGORY_SOURCE_MISMATCH", validate_entries(root, [entry])["errors"]
            )

    def test_summary_limitation_digest_and_private_path_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = _fixture(root)
            entry["summary"] = "Claim absent from reviewed source: C:\\private\\scan.jpg"
            entry["source_sha256"] = "0" * 64
            errors = validate_entries(root, [entry])["errors"]
            self.assertIn("CHANGELOG_SUMMARY_INVALID", errors)
            self.assertIn("CHANGELOG_SOURCE_DIGEST_MISMATCH", errors)
            self.assertIn("CHANGELOG_SUMMARY_NOT_IN_SOURCE_FRAGMENT", errors)

    def test_limitation_must_be_present_in_curated_fragment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = _fixture(root)
            entry["known_limitations"] = ["A limitation absent from the fragment."]
            errors = validate_entries(root, [entry])["errors"]
            self.assertIn("CHANGELOG_LIMITATION_NOT_IN_SOURCE_FRAGMENT", errors)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = _fixture(root)
            entry["known_limitations"] = ["Private production data path C:\\secret\\file"]
            self.assertIn(
                "CHANGELOG_LIMITATIONS_INVALID", validate_entries(root, [entry])["errors"]
            )
            entry["known_limitations"] = ["Private relative path ..\\secret\\file"]
            self.assertIn(
                "CHANGELOG_LIMITATIONS_INVALID", validate_entries(root, [entry])["errors"]
            )

    def test_unapproved_source_locations_and_path_traversal_reject(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = _fixture(root)
            entry["source_ref"] = "../outside.txt"
            self.assertIn(
                "CHANGELOG_SOURCE_FRAGMENT_UNAVAILABLE", validate_entries(root, [entry])["errors"]
            )
            entry["source_ref"] = "src/change.md"
            self.assertIn(
                "CHANGELOG_SOURCE_FRAGMENT_UNAVAILABLE", validate_entries(root, [entry])["errors"]
            )

    def test_rendering_groups_by_milestone_category_and_numeric_task_order(self) -> None:
        entries = [
            {
                "task_id": "PL-0010",
                "milestone": "M02",
                "category": "Fixed",
                "summary": "Second fix.",
                "known_limitations": [],
            },
            {
                "task_id": "PL-0009",
                "milestone": "M02",
                "category": "Added",
                "summary": "First addition.",
                "known_limitations": ["A limitation."],
            },
            {
                "task_id": "PL-0011",
                "milestone": "M01",
                "category": "Security",
                "summary": "Security fix.",
                "known_limitations": [],
            },
        ]
        rendered = render_changelog(entries, "1" * 40, _TRAIN)
        self.assertLess(rendered.index("## M01"), rendered.index("## M02"))
        self.assertLess(rendered.index("### Added"), rendered.index("### Fixed"))
        self.assertLess(rendered.index("PL-0009"), rendered.index("PL-0010"))
        self.assertIn("### Known limitations", rendered)
        self.assertIn("Studio: `0.1.0`", rendered)
        self.assertIn("not a release notice or release authorization", rendered)
        self.assertNotIn("coordination/sessions", rendered)

    def test_output_creation_refuses_existing_hard_link_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            tracked = root / "TASKS.md"
            tracked.write_text("owner content\n", encoding="utf-8")
            outside = Path(tmp) / "draft.md"
            try:
                os.link(tracked, outside)
            except OSError:
                self.skipTest("hard links are unavailable in this Windows environment")
            with self.assertRaisesRegex(ValueError, "CHANGELOG_OUTPUT_ALREADY_EXISTS_OR_LINKED"):
                _write_new_output(root, outside, "generated content\n")
            self.assertEqual(tracked.read_text(encoding="utf-8"), "owner content\n")

    def test_output_creation_rejects_reparse_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            parent = Path(tmp) / "linked-parent"
            root.mkdir()
            parent.mkdir()
            output = parent / "draft.md"
            is_symlink = Path.is_symlink

            def mark_parent_link(path: Path) -> bool:
                return path == parent or is_symlink(path)

            with patch.object(Path, "is_symlink", mark_parent_link):
                with self.assertRaisesRegex(ValueError, "CHANGELOG_OUTPUT_PARENT_LINKED"):
                    _write_new_output(root, output, "generated content\n")
            self.assertFalse(output.exists())

    def test_cli_rejects_incomplete_input_without_writing_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft = root / "draft.json"
            output = root / "output.md"
            draft.write_text("[]", encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = main([str(draft), "--repo", str(root), "--output", str(output)])
            self.assertEqual(result, 2)
            self.assertIn('"status": "BLOCKED"', stdout.getvalue())
            self.assertFalse(output.exists())

            repository = Path(__file__).resolve().parents[2]
            command = subprocess.run(
                [
                    sys.executable,
                    str(repository / "tools/release/offline_changelog.py"),
                    str(draft),
                    "--repo",
                    str(root),
                    "--output",
                    str(output),
                ],
                cwd=repository,
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(command.returncode, 2)
            self.assertIn('"status": "BLOCKED"', command.stdout)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
