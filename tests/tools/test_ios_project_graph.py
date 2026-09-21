import re
from pathlib import Path

PROJECT_PATH = Path("apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj")


def _configuration_line(project: str, identifier: str) -> str:
    return next(
        line for line in project.splitlines() if f"{identifier} /*" in line and "XCBuildConfiguration" in line
    )


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

    assert "A10000010000000000000012 /* PackLabCaptureTests.swift in Sources */" in project
    assert "A10001000000000000000001 /* PackLabCapture dependency */" in project
    assert not re.search(
        r"\b(?:DEVELOPMENT_TEAM|CODE_SIGN_IDENTITY|PROVISIONING_PROFILE(?:_SPECIFIER)?)\s*=",
        project,
    )
