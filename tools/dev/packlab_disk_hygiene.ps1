[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("inventory", "preflight", "post-test", "post-task")]
    [string]$Mode,
    [string]$RunTempPath,
    [string[]]$LegacyPytestRunIds = @(),
    [string]$JsonSummaryPath,
    [long]$ObservedPytestPeakBytes = 0,
    [long]$ObservedFixturePeakBytes = 0,
    [string]$ObservedFixturePeakPath,
    [long]$ObservedDisposablePeakBytes = 0,
    [switch]$MeasureInventoryBytes,
    [switch]$Apply,
    [switch]$PruneUv
)

$ErrorActionPreference = "Stop"
$script:PackLabTempRoot = Join-Path $env:TEMP "PackLab\pytest"
$script:LegacyPytestRoot = Join-Path $env:TEMP "pytest-of-sekip"
$script:MinimumFreeBytes = 40GB
$script:Summary = [ordered]@{
    mode = $Mode
    disk_free_before_bytes = [long]0
    disk_free_after_bytes = [long]0
    reclaimed_bytes = [long]0
    pytest_temp_peak_bytes = [long]$ObservedPytestPeakBytes
    largest_fixture_peak_bytes = [long]$ObservedFixturePeakBytes
    largest_fixture_peak_path = $ObservedFixturePeakPath
    disposable_packlab_peak_bytes = [long]$ObservedDisposablePeakBytes
    cleanup_categories = [ordered]@{}
    candidates = @()
    retained_paths = @()
    locked_paths = @()
    status = "IN_PROGRESS"
}

function Get-CanonicalPath([string]$Path) {
    return [System.IO.Path]::GetFullPath($Path).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
}

function Test-PathWithin([string]$Path, [string]$Root) {
    $fullPath = Get-CanonicalPath $Path
    $fullRoot = (Get-CanonicalPath $Root) + [System.IO.Path]::DirectorySeparatorChar
    return $fullPath.StartsWith($fullRoot, [System.StringComparison]::OrdinalIgnoreCase)
}

function Get-TreeBytes([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return [long]0 }
    $total = [long]0
    foreach ($file in Get-ChildItem -LiteralPath $Path -File -Force -Recurse -ErrorAction SilentlyContinue) {
        $total += [long]$file.Length
    }
    return $total
}

function Get-CDriveFreeBytes {
    $drive = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
    if ($null -eq $drive) { throw "Unable to measure free bytes on C:." }
    return [long]$drive.FreeSpace
}

function Write-Summary {
    if ([string]::IsNullOrWhiteSpace($JsonSummaryPath)) { return }
    $script:Summary.disk_free_after_bytes = Get-CDriveFreeBytes
    $parent = Split-Path -Parent $JsonSummaryPath
    if (-not [string]::IsNullOrWhiteSpace($parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    $json = $script:Summary | ConvertTo-Json -Depth 8
    [IO.File]::WriteAllText($JsonSummaryPath, $json + "`n", [Text.UTF8Encoding]::new($false))
    Write-Output "json_summary_path=$JsonSummaryPath"
}

function Get-PackLabInventory {
    $roots = @(
        (Join-Path $env:TEMP "PackLab"),
        $script:LegacyPytestRoot,
        (Join-Path $env:LOCALAPPDATA "uv\cache")
    )
    foreach ($root in $roots) {
        Write-Output "inventory_path=$root"
        if (Test-Path -LiteralPath $root -PathType Container) {
            if ($MeasureInventoryBytes) {
                $bytes = Get-TreeBytes $root
                Write-Output "inventory_bytes=$bytes"
            } else {
                $bytes = $null
                $entryCount = @(Get-ChildItem -LiteralPath $root -Force -ErrorAction SilentlyContinue).Count
                Write-Output "inventory_recursive_size=NOT_MEASURED use_-MeasureInventoryBytes_for_full_byte_walk"
                Write-Output "inventory_immediate_entry_count=$entryCount"
            }
            $script:Summary.candidates += [ordered]@{ path = $root; bytes = $bytes; action = "INVENTORY_ONLY" }
        } else {
            Write-Output "inventory_state=ABSENT"
        }
    }
    foreach ($ownerRoot in @((Join-Path $env:LOCALAPPDATA "PackLab\OwnerDev"), (Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) "PackLab\OwnerDev"))) {
        if (-not (Test-Path -LiteralPath $ownerRoot -PathType Container)) { continue }
        foreach ($child in Get-ChildItem -LiteralPath $ownerRoot -Directory -Force -ErrorAction SilentlyContinue) {
            if ($child.Name -in @("current", "releases", "logs", "launcher", "staging") -or $child.Name -match '^(previous-|stage-|current-stage-|refresh-)') {
                Write-Output "ownerdev_child=$($child.FullName)"
                $script:Summary.candidates += [ordered]@{ path = $child.FullName; bytes = $null; action = "OWNERDEV_INVENTORY_ONLY" }
                if ($child.Name -eq "current") {
                    $manifestPath = Join-Path $child.FullName "owner-dev-runtime.json"
                    if (Test-Path -LiteralPath $manifestPath -PathType Leaf) {
                        $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
                        Write-Output "ownerdev_current_runtime_id=$($manifest.runtime_id)"
                        Write-Output "ownerdev_current_smoke_status=$($manifest.smoke_status)"
                    }
                }
            }
        }
    }
}

function Get-ActiveTestProcesses {
    return @(Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -match '(?i)(pytest|mypy)' -and
        $_.Name -match '^(python|pythonw|pytest|mypy)(\.exe)?$'
    })
}

function Remove-ExactCandidate([string]$Path, [string]$ExpectedRoot, [long]$Bytes) {
    Write-Host "candidate_path=$Path"
    Write-Host "candidate_bytes=$Bytes"
    if (-not $Apply) {
        Write-Host "action=DRY_RUN"
        return [long]0
    }
    if (-not (Test-PathWithin $Path $ExpectedRoot)) {
        throw "Refusing path outside allowlisted root: $Path"
    }
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Refusing reparse point: $Path"
    }
    try {
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
        Write-Host "action=REMOVED"
        return $Bytes
    } catch {
        Write-Host "action=LOCKED_OR_DENIED"
        Write-Host "error=$($_.Exception.Message)"
        $script:Summary.locked_paths += $Path
        return [long]0
    }
}

function Remove-PackLabRun([string]$Path) {
    if (-not (Test-PathWithin $Path $script:PackLabTempRoot)) {
        throw "Refusing PackLab run outside its disposable root: $Path"
    }
    $ownerPath = Join-Path $Path ".packlab-run.json"
    if (-not (Test-Path -LiteralPath $ownerPath -PathType Leaf)) {
        throw "Refusing unmarked PackLab temp directory: $Path"
    }
    $owner = Get-Content -LiteralPath $ownerPath -Raw | ConvertFrom-Json
    if ([int]$owner.process_id -gt 0 -and (Get-Process -Id ([int]$owner.process_id) -ErrorAction SilentlyContinue)) {
        Write-Host "retained_active_run=$Path"
        return [long]0
    }
    $pathNeedle = (Get-CanonicalPath $Path) + [System.IO.Path]::DirectorySeparatorChar
    $activeOwners = @(Get-CimInstance Win32_Process | Where-Object {
        $_.ProcessId -ne $PID -and
        (($_.ExecutablePath -and $_.ExecutablePath.StartsWith($pathNeedle, [System.StringComparison]::OrdinalIgnoreCase)) -or
         ($_.CommandLine -and $_.CommandLine.IndexOf($pathNeedle, [System.StringComparison]::OrdinalIgnoreCase) -ge 0))
    })
    if ($activeOwners.Count -gt 0) {
        $activeOwners | ForEach-Object { Write-Host "retained_run_process_pid=$($_.ProcessId) command=$($_.CommandLine)" }
        return [long]0
    }
    $bytes = Get-TreeBytes $Path
    return Remove-ExactCandidate $Path $script:PackLabTempRoot $bytes
}

$freeBefore = Get-CDriveFreeBytes
$script:Summary.disk_free_before_bytes = $freeBefore
Write-Output "mode=$Mode"
Write-Output "disk_free_before_bytes=$freeBefore"
Write-Output "apply=$([bool]$Apply)"

if ($Mode -eq "preflight") {
    Write-Host "packlab_pytest_root=$script:PackLabTempRoot"
    Write-Host "packlab_pytest_root_bytes=$(Get-TreeBytes $script:PackLabTempRoot)"
    if ($freeBefore -lt $script:MinimumFreeBytes) {
        Write-Host "status=LOCAL_DISK_SPACE_BLOCKED"
        $script:Summary.status = "LOCAL_DISK_SPACE_BLOCKED"
        Write-Summary
        $global:LASTEXITCODE = 40
        return
    }
    Write-Host "status=DISK_PREFLIGHT_PASS"
    $script:Summary.status = "DISK_PREFLIGHT_PASS"
    Write-Summary
    $global:LASTEXITCODE = 0
    return
}

if ($Mode -eq "inventory") {
    Get-PackLabInventory
    $script:Summary.disk_free_after_bytes = Get-CDriveFreeBytes
    $script:Summary.status = "DISK_INVENTORY_PASS"
    Write-Output "disk_free_after_bytes=$($script:Summary.disk_free_after_bytes)"
    Write-Summary
    $global:LASTEXITCODE = 0
    return
}

$reclaimed = [long]0
$lockedOrDenied = [System.Collections.Generic.List[string]]::new()

if ($Mode -eq "post-test") {
    if ([string]::IsNullOrWhiteSpace($RunTempPath)) { throw "post-test requires -RunTempPath." }
    if (-not (Test-PathWithin $RunTempPath $script:PackLabTempRoot)) {
        throw "Refusing post-test path outside PackLab temp root: $RunTempPath"
    }
    $runBytes = Get-TreeBytes $RunTempPath
    $removedBytes = Remove-PackLabRun $RunTempPath
    $reclaimed += $removedBytes
    $script:Summary.cleanup_categories.packlab_pytest_temp = $removedBytes
    $script:Summary.candidates += [ordered]@{ path = $RunTempPath; bytes = $runBytes; action = $(if ($removedBytes -gt 0) { "REMOVED" } else { "RETAINED_OR_EMPTY" }) }
    if ($removedBytes -eq 0 -and (Test-Path -LiteralPath $RunTempPath)) { $script:Summary.retained_paths += $RunTempPath }
}

if ($Mode -eq "post-task") {
    if (Test-Path -LiteralPath $script:PackLabTempRoot -PathType Container) {
        Get-ChildItem -LiteralPath $script:PackLabTempRoot -Directory -Force |
            Where-Object { $_.Name -match '^run-[0-9]{8}T[0-9]{6}-[0-9a-f]{8}$' } |
            ForEach-Object { $reclaimed += Remove-PackLabRun $_.FullName }
    }

    if ($LegacyPytestRunIds.Count -gt 0) {
        $activeTests = Get-ActiveTestProcesses
        if ($activeTests.Count -gt 0) {
            $activeTests | ForEach-Object { Write-Host "retained_active_test_pid=$($_.ProcessId) command=$($_.CommandLine)" }
            Write-Host "legacy_cleanup=SKIPPED_ACTIVE_TEST_PROCESS"
        } else {
            foreach ($runId in $LegacyPytestRunIds) {
                if ($runId -notmatch '^[0-9]+$') { throw "Invalid legacy pytest run ID: $runId" }
                $candidate = Join-Path $script:LegacyPytestRoot "pytest-$runId"
                if (-not (Test-Path -LiteralPath $candidate -PathType Container)) { continue }
                $bytes = Get-TreeBytes $candidate
                $removedBytes = Remove-ExactCandidate $candidate $script:LegacyPytestRoot $bytes
                $reclaimed += $removedBytes
                $script:Summary.candidates += [ordered]@{ path = $candidate; bytes = $bytes; action = $(if ($removedBytes -gt 0) { "REMOVED" } else { "RETAINED_OR_EMPTY" }) }
                if ($removedBytes -eq 0 -and (Test-Path -LiteralPath $candidate)) { $script:Summary.retained_paths += $candidate }
            }
        }
    }

    if ($PruneUv) {
        $uvCacheRoot = Join-Path $env:LOCALAPPDATA "uv\cache"
        $uvBytesBefore = Get-TreeBytes $uvCacheRoot
        $script:Summary.cleanup_categories.uv_cache_before_bytes = $uvBytesBefore
        Write-Host "uv_cache_path=$uvCacheRoot"
        Write-Host "uv_cache_bytes_before=$uvBytesBefore"
        $activeUv = @(Get-CimInstance Win32_Process | Where-Object {
            ($_.ExecutablePath -and $_.ExecutablePath.StartsWith($uvCacheRoot, [System.StringComparison]::OrdinalIgnoreCase)) -or
            ($_.CommandLine -and $_.CommandLine.IndexOf($uvCacheRoot, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
        })
        if (-not $Apply) {
            Write-Host "uv_prune=DRY_RUN"
            Write-Host "uv_cache_bytes_after=$uvBytesBefore"
        } elseif ($activeUv.Count -gt 0) {
            $activeUv | ForEach-Object { Write-Host "uv_prune_skipped_active_pid=$($_.ProcessId) exe=$($_.ExecutablePath)" }
            Write-Host "uv_prune=SKIPPED_ACTIVE_CACHE_PROCESS"
            Write-Host "uv_cache_bytes_after=$uvBytesBefore"
        } else {
            $uv = Get-Command uv -ErrorAction SilentlyContinue
            if ($null -eq $uv) {
                Write-Host "uv_prune=UNAVAILABLE"
                Write-Host "uv_cache_bytes_after=$uvBytesBefore"
            } else {
                & $uv.Source cache prune
                $uvExit = $LASTEXITCODE
                Write-Host "uv_prune_exit_code=$uvExit"
                if ($uvExit -ne 0) { throw "uv cache prune failed with exit code $uvExit." }
                Write-Host "uv_cache_bytes_after=$(Get-TreeBytes $uvCacheRoot)"
                $script:Summary.cleanup_categories.uv_cache_after_bytes = Get-TreeBytes $uvCacheRoot
                $script:Summary.cleanup_categories.uv_cache_pruned_bytes = [Math]::Max([long]0, $uvBytesBefore - [long]$script:Summary.cleanup_categories.uv_cache_after_bytes)
            }
        }
    }
}

$freeAfter = Get-CDriveFreeBytes
Write-Host "disk_free_after_bytes=$freeAfter"
Write-Host "reclaimed_bytes=$reclaimed"
if ($freeAfter -lt $script:MinimumFreeBytes) {
    Write-Host "status=LOCAL_DISK_SPACE_BLOCKED"
    $script:Summary.status = "LOCAL_DISK_SPACE_BLOCKED"
    $script:Summary.disk_free_after_bytes = $freeAfter
    $script:Summary.reclaimed_bytes = $reclaimed
    Write-Summary
    $global:LASTEXITCODE = 40
    return
}
Write-Host "status=DISK_HYGIENE_PASS"
$script:Summary.status = "DISK_HYGIENE_PASS"
$script:Summary.disk_free_after_bytes = $freeAfter
$script:Summary.reclaimed_bytes = $reclaimed
Write-Summary
$global:LASTEXITCODE = 0
