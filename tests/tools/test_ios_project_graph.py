import re
from pathlib import Path

import pytest

PROJECT_PATH = Path("apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj")
TEST_SOURCE_PHASE_ID = "A10000200000000000000005"
TEST_SOURCE_BUILD_FILE_ID = "A10000010000000000000012"
TEST_TARGET_ID = "A10000400000000000000002"
TARGET_DEPENDENCY_ID = "A10001000000000000000001"


def _configuration_line(project: str, identifier: str) -> str:
    return next(
        line for line in project.splitlines() if f"{identifier} /*" in line and "XCBuildConfiguration" in line
    )


def _object_block(project: str, identifier: str) -> str:
    marker = re.search(
        rf"(?m)^\s*{re.escape(identifier)}\s+/\*.*?\*/\s*=\s*\{{",
        project,
    )
    assert marker is not None, f"PBX object {identifier} is missing"
    depth = 0
    for index in range(marker.start(), len(project)):
        if project[index] == "{":
            depth += 1
        elif project[index] == "}":
            depth -= 1
            if depth == 0:
                return project[marker.start() : index + 1]
    raise AssertionError(f"PBX object {identifier} is unterminated")


def _assert_relationships(project: str) -> None:
    test_sources_phase = _object_block(project, TEST_SOURCE_PHASE_ID)
    assert "PBXSourcesBuildPhase" in test_sources_phase
    assert (
        f"{TEST_SOURCE_BUILD_FILE_ID} /* PackLabCaptureTests.swift in Sources */"
        in test_sources_phase
    )

    test_target = _object_block(project, TEST_TARGET_ID)
    dependencies = re.search(r"dependencies\s*=\s*\((.*?)\);", test_target, re.DOTALL)
    assert dependencies is not None
    assert f"{TARGET_DEPENDENCY_ID} /* PackLabCapture dependency */" in dependencies.group(1)


def test_hosted_xctest_graph_is_durable_without_xcode(repo_root):
    project_path = repo_root / PROJECT_PATH
    project = project_path.read_text(encoding="utf-8")

    assert project_path.is_file()
    for identifier in (
        "A10000700000000000000001",  # PackLabCapture Debug
        "A10000700000000000000002",  # PackLabCapture Release
    ):
        app_configuration = _configuration_line(project, identifier)
        assert "ENABLE_TESTABILITY = YES;" in app_configuration

    expected_loader = 'BUNDLE_LOADER = "$(BUILT_PRODUCTS_DIR)/PackLabCapture.app/PackLabCapture";'
    expected_host = 'TEST_HOST = "$(BUNDLE_LOADER)";'
    for identifier in (
        "A10000700000000000000005",  # PackLabCaptureTests Debug
        "A10000700000000000000006",  # PackLabCaptureTests Release
    ):
        test_configuration = _configuration_line(project, identifier)
        assert expected_loader in test_configuration
        assert expected_host in test_configuration

    _assert_relationships(project)
    assert not re.search(
        r"\b(?:DEVELOPMENT_TEAM|CODE_SIGN_IDENTITY|PROVISIONING_PROFILE(?:_SPECIFIER)?)\s*=",
        project,
    )


def test_source_membership_guard_rejects_edge_removal_with_object_intact(repo_root):
    project = (repo_root / PROJECT_PATH).read_text(encoding="utf-8")
    source_edge = f"{TEST_SOURCE_BUILD_FILE_ID} /* PackLabCaptureTests.swift in Sources */,"
    mutated, replacements = re.subn(
        rf"(A10000200000000000000005 /\* Test Sources \*/.*?files = \()"
        rf"{re.escape(source_edge)}",
        r"\1",
        project,
        count=1,
        flags=re.DOTALL,
    )

    assert replacements == 1
    assert source_edge[:-1] in mutated
    with pytest.raises(AssertionError):
        _assert_relationships(mutated)


def test_target_dependency_guard_rejects_edge_removal_with_object_intact(repo_root):
    project = (repo_root / PROJECT_PATH).read_text(encoding="utf-8")
    dependency_edge = f"{TARGET_DEPENDENCY_ID} /* PackLabCapture dependency */,"
    mutated, replacements = re.subn(
        rf"(A10000400000000000000002 /\* PackLabCaptureTests \*/.*?dependencies\s*=\s*\()"
        rf"\s*{re.escape(dependency_edge)}",
        r"\1",
        project,
        count=1,
        flags=re.DOTALL,
    )

    assert replacements == 1
    assert dependency_edge[:-1] in mutated
    with pytest.raises(AssertionError):
        _assert_relationships(mutated)
