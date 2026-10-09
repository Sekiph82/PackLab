from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HYGIENE = ROOT / "tools" / "dev" / "packlab_disk_hygiene.ps1"
TEST_WRAPPER = ROOT / "tools" / "dev" / "run_packlab_tests.ps1"
POLICY = ROOT / "docs" / "development" / "PACKLAB_LOCAL_DISK_HYGIENE.md"


def test_disk_hygiene_helper_is_allowlisted_dry_run_and_fail_safe() -> None:
    helper = HYGIENE.read_text(encoding="utf-8")
    assert 'ValidateSet("inventory", "preflight", "post-test", "post-task")' in helper
    assert "$script:MinimumFreeBytes = 40GB" in helper
    assert '$script:PackLabTempRoot = Join-Path $env:TEMP "PackLab\\pytest"' in helper
    assert "[switch]$Apply" in helper
    assert "if (-not $Apply)" in helper
    assert "Test-PathWithin" in helper
    assert "ReparsePoint" in helper
    assert "Get-ActiveTestProcesses" in helper
    assert "LOCKED_OR_DENIED" in helper
    assert "LegacyPytestRunIds" in helper
    assert "uv cache prune" in helper
    assert "SKIPPED_ACTIVE_CACHE_PROCESS" in helper
    assert "Remove-Item -LiteralPath $Path -Recurse -Force" in helper
    assert "JsonSummaryPath" in helper and "ConvertTo-Json -Depth 8" in helper
    assert "Get-PackLabInventory" in helper
    assert "MeasureInventoryBytes" in helper
    assert "$script:MaximumDisposableBytes = 8GB" in helper
    assert "Get-DisposablePackLabPaths" in helper
    assert "Remove-OwnerDevSuperseded" in helper
    assert "Remove-ObsoleteAppDataOwnerDev" in helper
    assert "Test-DesktopOwnerDevBinding" in helper
    assert "ownerdev_superseded_release" in helper


def test_full_test_wrapper_owns_basetemp_and_cleans_in_finally() -> None:
    wrapper = TEST_WRAPPER.read_text(encoding="utf-8")
    assert '@("run", "--locked", "pytest")' in wrapper
    assert '@("--basetemp", $baseTemp)' in wrapper
    assert 'Join-Path $env:TEMP "PackLab\\pytest"' in wrapper
    assert "Do not pass --basetemp" in wrapper
    assert "$maxBaseTempBytes = 4GB" in wrapper
    assert "$maxFixtureBytes = 2GB" in wrapper
    assert "$maxDisposableBytes = 8GB" in wrapper
    assert "Get-TempTreeStats $baseTemp" in wrapper
    assert "PYTEST_DISK_BUDGET_EXCEEDED" in wrapper
    assert "TEST_FIXTURE_DISK_BUDGET_EXCEEDED" in wrapper
    assert "taskkill.exe /PID $proc.Id /T /F" in wrapper
    assert "Stop-PytestTree" in wrapper
    assert "PACKLAB_DISPOSABLE_DISK_BUDGET_EXCEEDED" in wrapper
    assert "Show-LargestTempEntries $baseTemp" in wrapper
    assert "try {" in wrapper
    assert "finally {" in wrapper
    assert "-Mode post-test -RunTempPath $runRoot -Apply" in wrapper
    assert "$exitCode = $proc.ExitCode" in wrapper
    assert "exit $exitCode" in wrapper


def test_disk_hygiene_policy_protects_owner_data_and_sets_space_floor() -> None:
    policy = POLICY.read_text(encoding="utf-8")
    assert "40 GiB" in policy
    assert "Desktop `PackLab.exe`" in policy
    assert "active/dirty/ambiguous worktrees" in policy
    assert "Hugging Face, Puppeteer, browser, GPU, and Codex runtime/cache" in policy
    assert "uv cache clean" in policy
    assert "OWNER DEV" in policy
