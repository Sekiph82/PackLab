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
    [switch]$PruneUv,
    [switch]$CleanupOwnerDev,
    [switch]$RemoveLegacyAppDataOwnerDev
)

$ErrorActionPreference = "Stop"
$script:PackLabTempRoot = Join-Path $env:TEMP "PackLab\pytest"
$script:LegacyPytestRoot = Join-Path $env:TEMP "pytest-of-sekip"
$script:MinimumFreeBytes = 40GB
$script:MaximumDisposableBytes = 8GB
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
    $pending = [System.Collections.Generic.Stack[string]]::new()
    $pending.Push((Get-CanonicalPath $Path))
    while ($pending.Count -gt 0) {
        $directory = $pending.Pop()
        try { $entries = [System.IO.Directory]::EnumerateFileSystemEntries($directory) }
        catch {
            $script:Summary.locked_paths += $directory
            continue
        }
        foreach ($entry in $entries) {
            try {
                $attributes = [System.IO.File]::GetAttributes($entry)
                if (($attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
                if (($attributes -band [System.IO.FileAttributes]::Directory) -ne 0) { $pending.Push($entry) }
                else { $total += [long]([System.IO.FileInfo]::new($entry)).Length }
            } catch {
                $script:Summary.locked_paths += $entry
            }
        }
    }
    return $total
}

function Get-CDriveFreeBytes {
    $drive = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
    if ($null -eq $drive) { throw "Unable to measure free bytes on C:." }
    return [long]$drive.FreeSpace
}

function Get-DisposablePackLabPaths {
    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
    $desktopOwnerRoot = Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) "PackLab\OwnerDev"
    $appDataOwnerRoot = Join-Path $env:LOCALAPPDATA "PackLab\OwnerDev"
    return @(
        (Join-Path $env:TEMP "PackLab"),
        (Join-Path $repoRoot "build"),
        (Join-Path $repoRoot "dist"),
        (Join-Path $repoRoot "staging"),
        (Join-Path $repoRoot "reports\_local\pytest"),
        (Join-Path $desktopOwnerRoot "staging"),
        (Join-Path $desktopOwnerRoot "temp"),
        (Join-Path $appDataOwnerRoot "staging"),
        (Join-Path $appDataOwnerRoot "temp")
    )
}

function Get-DisposablePackLabBytes {
    $total = [long]0
    foreach ($path in Get-DisposablePackLabPaths) { $total += Get-TreeBytes $path }
    return $total
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
                $bytes = if ($MeasureInventoryBytes) { Get-TreeBytes $child.FullName } else { $null }
                if ($MeasureInventoryBytes) { Write-Output "ownerdev_child_bytes=$bytes" }
                $script:Summary.candidates += [ordered]@{ path = $child.FullName; bytes = $bytes; action = "OWNERDEV_INVENTORY_ONLY" }
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

function Test-OwnerDevPathActive([string]$OwnerRoot) {
    $needle = (Get-CanonicalPath $OwnerRoot) + [System.IO.Path]::DirectorySeparatorChar
    return @(Get-CimInstance Win32_Process | Where-Object {
        ($_.ExecutablePath -and $_.ExecutablePath.StartsWith($needle, [System.StringComparison]::OrdinalIgnoreCase)) -or
        ($_.CommandLine -and $_.CommandLine.IndexOf($needle, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
    })
}

function Get-OwnerDevManifest([string]$Path) {
    $manifestPath = Join-Path $Path "owner-dev-runtime.json"
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { return $null }
    try {
        $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
        if ($manifest.runtime_id -notmatch '^[0-9a-f]{40}-[0-9a-f]{32}$' -or
            $manifest.source_commit -notmatch '^[0-9a-f]{40}$' -or
            $manifest.smoke_status -ne 'PASS') { return $null }
        return $manifest
    } catch { return $null }
}

function Test-DesktopOwnerDevBinding([string]$OwnerRoot) {
    $expectedOwnerRoot = Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) "PackLab\OwnerDev"
    if (-not [string]::Equals((Get-CanonicalPath $OwnerRoot), (Get-CanonicalPath $expectedOwnerRoot), [System.StringComparison]::OrdinalIgnoreCase)) { return $false }
    $current = Get-OwnerDevManifest (Join-Path $OwnerRoot "current")
    $fingerprintPath = Join-Path $OwnerRoot "launcher\PackLab.build.json"
    $launcherPath = Join-Path $OwnerRoot "launcher\PackLab.exe"
    $desktopExe = Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) "PackLab.exe"
    if ($null -eq $current -or -not (Test-Path -LiteralPath $fingerprintPath -PathType Leaf) -or
        -not (Test-Path -LiteralPath $launcherPath -PathType Leaf) -or -not (Test-Path -LiteralPath $desktopExe -PathType Leaf)) { return $false }
    try { $fingerprint = Get-Content -LiteralPath $fingerprintPath -Raw | ConvertFrom-Json }
    catch { return $false }
    $launcherHash = (Get-FileHash -LiteralPath $launcherPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $desktopHash = (Get-FileHash -LiteralPath $desktopExe -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($fingerprint.runtime_id -ne $current.runtime_id -or $fingerprint.exe_sha256 -ne $launcherHash -or $launcherHash -ne $desktopHash) { return $false }
    $programs = [Environment]::GetFolderPath('Programs')
    $shell = New-Object -ComObject WScript.Shell
    $shortcuts = @(Get-ChildItem -LiteralPath (Join-Path $programs "PackLab") -Filter "*.lnk" -File -ErrorAction SilentlyContinue)
    $targets = @($shortcuts | ForEach-Object { $shell.CreateShortcut($_.FullName).TargetPath })
    return ($targets -contains $launcherPath)
}

function Remove-OwnerDevSuperseded([string]$OwnerRoot) {
    if (-not (Test-Path -LiteralPath $OwnerRoot -PathType Container)) { return }
    if (-not (Test-DesktopOwnerDevBinding $OwnerRoot)) {
        Write-Host "ownerdev_retention=SKIPPED_DESKTOP_LAUNCHER_BINDING_UNVERIFIED path=$OwnerRoot"
        $script:Summary.retained_paths += $OwnerRoot
        return
    }
    $currentPath = Join-Path $OwnerRoot "current"
    $current = Get-OwnerDevManifest $currentPath
    if ($null -eq $current) {
        Write-Host "ownerdev_retention=SKIPPED_CURRENT_MANIFEST_UNVERIFIED path=$OwnerRoot"
        $script:Summary.retained_paths += $OwnerRoot
        return
    }
    if ((Test-OwnerDevPathActive $OwnerRoot).Count -gt 0) {
        Write-Host "ownerdev_retention=SKIPPED_ACTIVE_RUNTIME path=$OwnerRoot"
        $script:Summary.retained_paths += $OwnerRoot
        return
    }
    $releases = Join-Path $OwnerRoot "releases"
    $releaseCandidates = @()
    if (Test-Path -LiteralPath $releases -PathType Container) {
        foreach ($release in Get-ChildItem -LiteralPath $releases -Directory -Force) {
            $manifest = Get-OwnerDevManifest $release.FullName
            if ($null -ne $manifest -and $release.Name -eq $manifest.runtime_id) {
                $releaseCandidates += [pscustomobject]@{ Path = $release.FullName; Manifest = $manifest; Modified = $release.LastWriteTimeUtc }
            } else {
                Write-Host "ownerdev_retained_unverified_release=$($release.FullName)"
                $script:Summary.retained_paths += $release.FullName
            }
        }
    }
    $previous = $releaseCandidates | Where-Object { $_.Manifest.runtime_id -ne $current.runtime_id -and $_.Manifest.source_commit -ne $current.source_commit } | Sort-Object { [DateTime]$_.Manifest.refreshed_utc } -Descending | Select-Object -First 1
    $keepIds = @($current.runtime_id)
    if ($previous) { $keepIds += $previous.Manifest.runtime_id }
    Write-Host "ownerdev_retained_runtime_ids=$($keepIds -join ',')"
    foreach ($release in $releaseCandidates) {
        if ($release.Manifest.runtime_id -in $keepIds) {
            Write-Host "ownerdev_retained_runtime=$($release.Manifest.runtime_id) reason=$(if ($release.Manifest.runtime_id -eq $current.runtime_id) { 'current' } else { 'previous_good' })"
            continue
        }
        $path = $release.Path
        $bytes = Get-TreeBytes $path
        $removed = Remove-ExactCandidate $path $releases $bytes
        $reclaimed += $removed
        $script:Summary.candidates += [ordered]@{ path = $path; bytes = $bytes; category = "ownerdev_superseded_release"; action = $(if ($removed -gt 0) { "REMOVED" } else { "RETAINED_OR_EMPTY" }) }
        $script:Summary.cleanup_categories.ownerdev_superseded_releases = [long]$script:Summary.cleanup_categories.ownerdev_superseded_releases + $removed
        if ($removed -eq 0 -and (Test-Path -LiteralPath $path)) { $script:Summary.retained_paths += $path }
    }
    if ($previous) { $snapshotKeepId = $previous.Manifest.runtime_id }
    else { $snapshotKeepId = $null }
    foreach ($snapshot in Get-ChildItem -LiteralPath $OwnerRoot -Directory -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^previous-' }) {
        $manifest = Get-OwnerDevManifest $snapshot.FullName
        if ($null -eq $manifest) {
            Write-Host "ownerdev_retained_unverified_rollback=$($snapshot.FullName)"
            $script:Summary.retained_paths += $snapshot.FullName
            continue
        }
        if ($snapshotKeepId -and $manifest.runtime_id -eq $snapshotKeepId) {
            Write-Host "ownerdev_retained_previous_good_snapshot=$($snapshot.FullName)"
            $snapshotKeepId = $null
            continue
        }
        $path = $snapshot.FullName
        $bytes = Get-TreeBytes $path
        $removed = Remove-ExactCandidate $path $OwnerRoot $bytes
        $reclaimed += $removed
        $script:Summary.candidates += [ordered]@{ path = $path; bytes = $bytes; category = "ownerdev_superseded_rollback"; action = $(if ($removed -gt 0) { "REMOVED" } else { "RETAINED_OR_EMPTY" }) }
        $script:Summary.cleanup_categories.ownerdev_superseded_rollbacks = [long]$script:Summary.cleanup_categories.ownerdev_superseded_rollbacks + $removed
        if ($removed -eq 0 -and (Test-Path -LiteralPath $path)) { $script:Summary.retained_paths += $path }
    }
}

function Remove-ObsoleteAppDataOwnerDev {
    $appRoot = Join-Path $env:LOCALAPPDATA "PackLab\OwnerDev"
    $desktopRoot = Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) "PackLab\OwnerDev"
    if (-not (Test-Path -LiteralPath $appRoot -PathType Container)) { return }
    $desktopCurrent = Get-OwnerDevManifest (Join-Path $desktopRoot "current")
    $desktopLauncher = Join-Path $desktopRoot "launcher\PackLab.exe"
    $desktopBuild = Join-Path $desktopRoot "launcher\PackLab.build.json"
    $desktopExe = Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) "PackLab.exe"
    if ($null -eq $desktopCurrent -or -not (Test-Path -LiteralPath $desktopLauncher -PathType Leaf) -or
        -not (Test-Path -LiteralPath $desktopBuild -PathType Leaf) -or -not (Test-Path -LiteralPath $desktopExe -PathType Leaf)) {
        Write-Host "legacy_appdata_ownerdev=RETAINED_DESKTOP_OWNERDEV_NOT_VERIFIED"
        $script:Summary.retained_paths += $appRoot
        return
    }
    $fingerprint = Get-Content -LiteralPath $desktopBuild -Raw | ConvertFrom-Json
    $hash = (Get-FileHash -LiteralPath $desktopLauncher -Algorithm SHA256).Hash.ToLowerInvariant()
    $desktopExeHash = (Get-FileHash -LiteralPath $desktopExe -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($fingerprint.runtime_id -ne $desktopCurrent.runtime_id -or $fingerprint.exe_sha256 -ne $hash -or $hash -ne $desktopExeHash) {
        Write-Host "legacy_appdata_ownerdev=RETAINED_DESKTOP_OWNERDEV_IDENTITY_MISMATCH"
        $script:Summary.retained_paths += $appRoot
        return
    }
    $programs = [Environment]::GetFolderPath('Programs')
    $shell = New-Object -ComObject WScript.Shell
    $shortcuts = @(Get-ChildItem -LiteralPath (Join-Path $programs "PackLab") -Filter "*.lnk" -File -ErrorAction SilentlyContinue)
    $targets = @($shortcuts | ForEach-Object { $shell.CreateShortcut($_.FullName).TargetPath })
    if ($targets -notcontains $desktopLauncher) {
        Write-Host "legacy_appdata_ownerdev=RETAINED_ACTIVE_SHORTCUT_NOT_VERIFIED"
        $script:Summary.retained_paths += $appRoot
        return
    }
    if ((Test-OwnerDevPathActive $appRoot).Count -gt 0) {
        Write-Host "legacy_appdata_ownerdev=RETAINED_ACTIVE_PROCESS"
        $script:Summary.retained_paths += $appRoot
        return
    }
    $allowedNames = @("branding", "current", "launcher", "logs", "releases", "staging", "temp")
    $unexpected = @(Get-ChildItem -LiteralPath $appRoot -Force | Where-Object { $_.Name -notin $allowedNames -and $_.Name -notmatch '^(previous-|current-stage-|stage-|refresh-)' })
    if ($unexpected.Count -gt 0) {
        $unexpected | ForEach-Object { Write-Host "legacy_appdata_ownerdev=RETAINED_UNEXPECTED_CHILD path=$($_.FullName)" }
        $script:Summary.retained_paths += $appRoot
        return
    }
    $item = Get-Item -LiteralPath $appRoot -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        Write-Host "legacy_appdata_ownerdev=RETAINED_REPARSE_POINT"
        $script:Summary.retained_paths += $appRoot
        return
    }
    $bytes = Get-TreeBytes $appRoot
    $removed = Remove-ExactCandidate $appRoot (Join-Path $env:LOCALAPPDATA "PackLab") $bytes
    $reclaimed += $removed
    $script:Summary.cleanup_categories.legacy_appdata_ownerdev = [long]$script:Summary.cleanup_categories.legacy_appdata_ownerdev + $removed
    $script:Summary.candidates += [ordered]@{ path = $appRoot; bytes = $bytes; category = "legacy_appdata_ownerdev"; action = $(if ($removed -gt 0) { "REMOVED" } else { "RETAINED_OR_EMPTY" }) }
    if ($removed -eq 0 -and (Test-Path -LiteralPath $appRoot)) { $script:Summary.retained_paths += $appRoot }
}

$freeBefore = Get-CDriveFreeBytes
$script:Summary.disk_free_before_bytes = $freeBefore
Write-Output "mode=$Mode"
Write-Output "disk_free_before_bytes=$freeBefore"
Write-Output "apply=$([bool]$Apply)"

if ($Mode -eq "preflight") {
    Write-Host "packlab_pytest_root=$script:PackLabTempRoot"
    $disposableBytes = Get-DisposablePackLabBytes
    $script:Summary.disposable_packlab_peak_bytes = $disposableBytes
    Write-Host "disposable_packlab_bytes=$disposableBytes"
    if ($freeBefore -lt $script:MinimumFreeBytes) {
        Write-Host "status=LOCAL_DISK_SPACE_BLOCKED"
        $script:Summary.status = "LOCAL_DISK_SPACE_BLOCKED"
        Write-Summary
        $global:LASTEXITCODE = 40
        return
    }
    if ($disposableBytes -gt $script:MaximumDisposableBytes) {
        Write-Host "status=PACKLAB_DISPOSABLE_DISK_BUDGET_EXCEEDED"
        $script:Summary.status = "PACKLAB_DISPOSABLE_DISK_BUDGET_EXCEEDED"
        Write-Summary
        $global:LASTEXITCODE = 41
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

    if ($CleanupOwnerDev) {
        $desktopOwnerRoot = Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) "PackLab\OwnerDev"
        Remove-OwnerDevSuperseded $desktopOwnerRoot
        if ($RemoveLegacyAppDataOwnerDev) {
            Remove-ObsoleteAppDataOwnerDev
        }
    }

    if ($Apply) {
        foreach ($root in @((Join-Path $env:TEMP "PackLab\staging"), (Join-Path $env:LOCALAPPDATA "PackLab\OwnerDev\staging"), (Join-Path $env:LOCALAPPDATA "PackLab\OwnerDev\temp"), (Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) "PackLab\OwnerDev\staging"), (Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) "PackLab\OwnerDev\temp"))) {
            if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
            foreach ($candidate in Get-ChildItem -LiteralPath $root -Directory -Force -ErrorAction SilentlyContinue) {
                $markerPath = Join-Path $candidate.FullName ".packlab-disposable.json"
                if (-not (Test-Path -LiteralPath $markerPath -PathType Leaf)) {
                    $script:Summary.retained_paths += $candidate.FullName
                    Write-Host "retained_unmarked_disposable=$($candidate.FullName)"
                    continue
                }
                $bytes = Get-TreeBytes $candidate.FullName
                $removedBytes = Remove-ExactCandidate $candidate.FullName $root $bytes
                $reclaimed += $removedBytes
                $script:Summary.candidates += [ordered]@{ path = $candidate.FullName; bytes = $bytes; action = $(if ($removedBytes -gt 0) { "REMOVED" } else { "RETAINED_OR_EMPTY" }) }
                if ($removedBytes -eq 0 -and (Test-Path -LiteralPath $candidate.FullName)) { $script:Summary.retained_paths += $candidate.FullName }
            }
        }
    }

    if ($PruneUv) {
        $uvCacheRoot = Join-Path $env:LOCALAPPDATA "uv\cache"
        Write-Host "uv_cache_path=$uvCacheRoot"
        $activeUv = @(Get-CimInstance Win32_Process | Where-Object {
            ($_.ExecutablePath -and $_.ExecutablePath.StartsWith($uvCacheRoot, [System.StringComparison]::OrdinalIgnoreCase)) -or
            ($_.CommandLine -and $_.CommandLine.IndexOf($uvCacheRoot, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
        })
        if ($Apply -and $activeUv.Count -gt 0) {
            $script:Summary.cleanup_categories.uv_cache_before_bytes = "NOT_MEASURED_ACTIVE_CACHE_PROCESS"
            $script:Summary.cleanup_categories.uv_cache_after_bytes = "NOT_MEASURED_ACTIVE_CACHE_PROCESS"
            $script:Summary.cleanup_categories.uv_active_process_count = $activeUv.Count
            Write-Host "uv_active_process_count=$($activeUv.Count)"
            $activeUv | Select-Object -First 8 | ForEach-Object { Write-Host "uv_prune_active_process_sample=$($_.ProcessId) $($_.Name) $($_.ExecutablePath)" }
            Write-Host "uv_cache_bytes_before=NOT_MEASURED_ACTIVE_CACHE_PROCESS"
            Write-Host "uv_prune=SKIPPED_ACTIVE_CACHE_PROCESS"
            Write-Host "uv_cache_bytes_after=NOT_MEASURED_ACTIVE_CACHE_PROCESS"
        } else {
            $uvBytesBefore = Get-TreeBytes $uvCacheRoot
            $script:Summary.cleanup_categories.uv_cache_before_bytes = $uvBytesBefore
            Write-Host "uv_cache_bytes_before=$uvBytesBefore"
            if (-not $Apply) {
            Write-Host "uv_prune=DRY_RUN"
            Write-Host "uv_cache_bytes_after=$uvBytesBefore"
                $script:Summary.cleanup_categories.uv_cache_after_bytes = $uvBytesBefore
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
}

$freeAfter = Get-CDriveFreeBytes
$disposableAfter = Get-DisposablePackLabBytes
$script:Summary.disposable_packlab_peak_bytes = [Math]::Max([long]$script:Summary.disposable_packlab_peak_bytes, $disposableAfter)
Write-Host "disk_free_after_bytes=$freeAfter"
Write-Host "disposable_packlab_bytes_after=$disposableAfter"
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
if ($Mode -eq "post-task" -and $disposableAfter -gt $script:MaximumDisposableBytes) {
    Write-Host "status=PACKLAB_DISPOSABLE_DISK_BUDGET_EXCEEDED"
    $script:Summary.status = "PACKLAB_DISPOSABLE_DISK_BUDGET_EXCEEDED"
    $script:Summary.disk_free_after_bytes = $freeAfter
    $script:Summary.reclaimed_bytes = $reclaimed
    Write-Summary
    $global:LASTEXITCODE = 41
    return
}
Write-Host "status=DISK_HYGIENE_PASS"
$script:Summary.status = "DISK_HYGIENE_PASS"
$script:Summary.disk_free_after_bytes = $freeAfter
$script:Summary.reclaimed_bytes = $reclaimed
Write-Summary
$global:LASTEXITCODE = 0
