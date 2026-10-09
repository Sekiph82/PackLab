[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs = @(),
    [switch]$ContractTestMode,
    [string]$ContractRoot,
    [ValidateSet("quiet", "stdout-eof", "nonzero", "base-over", "fixture-over", "staging-over", "measurement-failure")]
    [string]$ContractScenario = "quiet",
    [string]$ContractPython,
    [long]$ContractMaxBaseTempBytes = 0,
    [long]$ContractMaxFixtureBytes = 0,
    [long]$ContractMaxDisposableBytes = 0,
    [switch]$ContractInjectMeasurementFailure
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$hygiene = Join-Path $PSScriptRoot "packlab_disk_hygiene.ps1"
$productionTempRoot = Join-Path $env:TEMP "PackLab\pytest"
$diagnosticsRoot = Join-Path $repoRoot "reports\_local\pytest"
$summaryRoot = Join-Path $repoRoot "reports\_local\disk-hygiene"
$maxBaseTempBytes = 4GB
$maxFixtureBytes = 2GB
$maxDisposableBytes = 8GB
$minimumFreeBytes = 40GB
$maxMeasurementMilliseconds = 2000
$maxMeasurementEntries = 100000
$gracefulStopSeconds = 10
$finalStopWaitMilliseconds = 10000
$pollMilliseconds = 500
$exitCode = 1
$quotaTriggered = $false
$quotaMessage = ""
$peakTempBytes = [long]0
$peakFixtureBytes = [long]0
$peakFixturePath = ""
$peakDisposableBytes = [long]0
$diskFreeBeforeBytes = [long]0
$proc = $null
$stdoutTask = $null
$stderrTask = $null
$tail = [System.Collections.Generic.Queue[string]]::new()

if ($ContractTestMode) {
    $contractAllowedRoot = Join-Path $env:TEMP "PackLab\runner-contract"
    $contractFullRoot = [System.IO.Path]::GetFullPath($ContractRoot).TrimEnd('\')
    $contractFullAllowed = [System.IO.Path]::GetFullPath($contractAllowedRoot).TrimEnd('\') + '\'
    if (-not $contractFullRoot.StartsWith($contractFullAllowed, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Contract test root must be a child of $contractAllowedRoot."
    }
    if (-not (Test-Path -LiteralPath $contractFullRoot -PathType Container)) { throw "Contract test root is missing." }
    if (([System.IO.File]::GetAttributes($contractFullRoot) -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Contract test root cannot be a reparse point."
    }
    if ([string]::IsNullOrWhiteSpace($ContractPython) -or -not (Test-Path -LiteralPath $ContractPython -PathType Leaf)) {
        throw "Contract test mode requires an existing Python executable."
    }
    if ($ContractMaxBaseTempBytes -le 0 -or $ContractMaxBaseTempBytes -gt $maxBaseTempBytes -or
        $ContractMaxFixtureBytes -le 0 -or $ContractMaxFixtureBytes -gt $maxFixtureBytes -or
        $ContractMaxDisposableBytes -le 0 -or $ContractMaxDisposableBytes -gt $maxDisposableBytes) {
        throw "Contract limits must be positive and cannot exceed production limits."
    }
    if ($PytestArgs.Count -gt 0) { throw "Contract test mode does not accept pytest arguments." }
    $maxBaseTempBytes = $ContractMaxBaseTempBytes
    $maxFixtureBytes = $ContractMaxFixtureBytes
    $maxDisposableBytes = $ContractMaxDisposableBytes
    $pollMilliseconds = 25
    $gracefulStopSeconds = 1
    $finalStopWaitMilliseconds = 3000
    $tempRoot = $contractFullRoot
    $contractChild = Join-Path $repoRoot "tests\ci\packlab_test_runner_child.py"
    if (-not (Test-Path -LiteralPath $contractChild -PathType Leaf)) { throw "Contract child fixture is missing." }
    $runId = "run-contract-{0}" -f ([guid]::NewGuid().ToString("N"))
    $runRoot = Join-Path $tempRoot $runId
    $baseTemp = Join-Path $runRoot "pytest"
    $contractStagingRoot = Join-Path $tempRoot "staging"
} else {
    $tempRoot = Join-Path $env:TEMP "PackLab"
    $runId = "run-{0}-{1}" -f (Get-Date -Format "yyyyMMdd'T'HHmmss"), ([guid]::NewGuid().ToString("N").Substring(0, 8))
    $runRoot = Join-Path $productionTempRoot $runId
    $baseTemp = Join-Path $runRoot "pytest"
    $contractChild = $null
    $contractStagingRoot = $null
}

$diagnosticsPath = Join-Path $diagnosticsRoot "$runId.txt"
$summaryPath = Join-Path $summaryRoot "$runId.json"
$ownerPath = Join-Path $runRoot ".packlab-run.json"

function Add-OutputLine([string]$Line) {
    if ($null -eq $Line) { return }
    Write-Output $Line
    $tail.Enqueue($Line)
    while ($tail.Count -gt 200) { [void]$tail.Dequeue() }
}

function ConvertTo-WindowsArgument([string]$Value) {
    if ($Value.Length -gt 0 -and $Value -notmatch '[\s"]') { return $Value }
    $builder = [System.Text.StringBuilder]::new()
    [void]$builder.Append('"')
    $slashes = 0
    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq '\') { $slashes++; continue }
        if ($character -eq '"') {
            [void]$builder.Append(('\' * (2 * $slashes + 1)))
            [void]$builder.Append('"')
            $slashes = 0
            continue
        }
        if ($slashes -gt 0) { [void]$builder.Append(('\' * $slashes)); $slashes = 0 }
        [void]$builder.Append($character)
    }
    if ($slashes -gt 0) { [void]$builder.Append(('\' * (2 * $slashes))) }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function Get-PackLabDisposableRoots {
    if ($ContractTestMode) { return @($tempRoot) }
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

function Get-DiskSnapshot {
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $seenRoots = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $total = [long]0
    $baseTempBytes = [long]0
    $fixtureSizes = @{}
    $basePrefix = [System.IO.Path]::GetFullPath($baseTemp).TrimEnd('\') + '\'
    $entryCount = 0
    foreach ($rootValue in Get-PackLabDisposableRoots) {
        $root = [System.IO.Path]::GetFullPath($rootValue).TrimEnd('\')
        if (-not $seenRoots.Add($root)) { continue }
        if (-not [System.IO.Directory]::Exists($root)) {
            try {
                $rootAttributes = [System.IO.File]::GetAttributes($root)
                if (($rootAttributes -band [System.IO.FileAttributes]::Directory) -eq 0) {
                    throw "PACKLAB_DISPOSABLE_MEASUREMENT_FAILED path=$root reason=Configured_root_is_not_a_directory"
                }
            } catch [System.IO.FileNotFoundException] { continue }
            catch [System.IO.DirectoryNotFoundException] { continue }
            catch { throw "PACKLAB_DISPOSABLE_MEASUREMENT_FAILED path=$root reason=$($_.Exception.Message)" }
        }
        try { $rootAttributes = [System.IO.File]::GetAttributes($root) }
        catch { throw "PACKLAB_DISPOSABLE_MEASUREMENT_FAILED path=$root reason=$($_.Exception.Message)" }
        if (($rootAttributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "PACKLAB_DISPOSABLE_MEASUREMENT_FAILED path=$root reason=Configured_root_is_a_reparse_point"
        }
        $pending = [System.Collections.Generic.Stack[string]]::new()
        $pending.Push($root)
        while ($pending.Count -gt 0) {
            if ($timer.ElapsedMilliseconds -gt $maxMeasurementMilliseconds) {
                throw "PACKLAB_DISPOSABLE_MEASUREMENT_TIMEOUT elapsed_ms=$($timer.ElapsedMilliseconds) limit_ms=$maxMeasurementMilliseconds"
            }
            $directory = $pending.Pop()
            $enumerator = $null
            try {
                $enumerator = [System.IO.Directory]::EnumerateFileSystemEntries($directory).GetEnumerator()
                while ($enumerator.MoveNext()) {
                    $entryCount++
                    if ($entryCount -gt $maxMeasurementEntries) {
                        throw "PACKLAB_DISPOSABLE_MEASUREMENT_ENTRY_LIMIT entries=$entryCount limit=$maxMeasurementEntries"
                    }
                    if (($entryCount % 256) -eq 0 -and $timer.ElapsedMilliseconds -gt $maxMeasurementMilliseconds) {
                        throw "PACKLAB_DISPOSABLE_MEASUREMENT_TIMEOUT elapsed_ms=$($timer.ElapsedMilliseconds) limit_ms=$maxMeasurementMilliseconds"
                    }
                    $entry = [string]$enumerator.Current
                    try { $attributes = [System.IO.File]::GetAttributes($entry) }
                    catch [System.IO.FileNotFoundException] { continue }
                    catch [System.IO.DirectoryNotFoundException] { continue }
                    if (($attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
                    if (($attributes -band [System.IO.FileAttributes]::Directory) -ne 0) {
                        $pending.Push($entry)
                        continue
                    }
                    try { $length = [long]([System.IO.FileInfo]::new($entry)).Length }
                    catch [System.IO.FileNotFoundException] { continue }
                    catch [System.IO.DirectoryNotFoundException] { continue }
                    $total += $length
                    if ($entry.StartsWith($basePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
                        $baseTempBytes += $length
                        $relative = $entry.Substring($basePrefix.Length)
                        $parts = $relative -split '[\\/]'
                        $fixtureKey = if ($parts.Count -gt 1 -and $parts[0] -match '^pytest-') { Join-Path $parts[0] $parts[1] } else { $parts[0] }
                        $fixtureSizes[$fixtureKey] = [long]$fixtureSizes[$fixtureKey] + $length
                    }
                }
            } catch {
                throw "PACKLAB_DISPOSABLE_MEASUREMENT_FAILED path=$directory reason=$($_.Exception.Message)"
            } finally {
                if ($enumerator -is [System.IDisposable]) { $enumerator.Dispose() }
            }
        }
    }
    if ($ContractInjectMeasurementFailure -and (Test-Path -LiteralPath (Join-Path $runRoot "inject-measurement-failure"))) {
        throw "PACKLAB_DISPOSABLE_MEASUREMENT_FAILED injected_contract_fault=true"
    }
    $largest = $fixtureSizes.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 1
    $freeBytes = [long]0
    if (-not $ContractTestMode) {
        $drive = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
        if ($null -eq $drive) { throw "PACKLAB_DISPOSABLE_MEASUREMENT_FAILED reason=Unable_to_measure_C_drive_free_bytes" }
        $freeBytes = [long]$drive.FreeSpace
    }
    return [pscustomobject]@{
        DisposableBytes = $total
        BaseTempBytes = $baseTempBytes
        LargestFixtureBytes = [long]$(if ($largest) { $largest.Value } else { 0 })
        LargestFixturePath = [string]$(if ($largest) { $largest.Key } else { "" })
        DiskFreeBytes = $freeBytes
        ScanMilliseconds = $timer.ElapsedMilliseconds
        Entries = $entryCount
    }
}

function Stop-PytestTree {
    if (-not $proc -or $proc.HasExited) { return }
    & taskkill.exe /PID $proc.Id /T 2>&1 | ForEach-Object { Write-Output $_ }
    $deadline = [DateTime]::UtcNow.AddSeconds($gracefulStopSeconds)
    while (-not $proc.HasExited -and [DateTime]::UtcNow -lt $deadline) { Start-Sleep -Milliseconds 250 }
    if (-not $proc.HasExited) {
        Write-Output "pytest_tree_graceful_stop_timeout=true"
        & taskkill.exe /PID $proc.Id /T /F 2>&1 | ForEach-Object { Write-Output $_ }
        try { if (-not $proc.HasExited) { $proc.Kill() } } catch { }
    }
    try { $proc.WaitForExit($finalStopWaitMilliseconds) | Out-Null } catch { }
}

function Show-LargestTempEntries([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return }
    $fileSizes = @{}
    $directorySizes = @{}
    $prefix = (Resolve-Path -LiteralPath $Path).Path.TrimEnd('\') + '\'
    Get-ChildItem -LiteralPath $Path -File -Force -Recurse -ErrorAction Stop | ForEach-Object {
        $fileSizes[$_.FullName] = [long]$_.Length
        $relative = $_.FullName.Substring($prefix.Length)
        $first = ($relative -split '[\\/]')[0]
        $directorySizes[$first] = [long]$directorySizes[$first] + [long]$_.Length
    }
    foreach ($entry in ($directorySizes.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 10)) {
        Write-Output "largest_temp_directory=$($entry.Value) $($entry.Key)"
    }
    foreach ($entry in ($fileSizes.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 10)) {
        Write-Output "largest_temp_file=$($entry.Value) $($entry.Key)"
    }
}

if (-not $ContractTestMode -and ($PytestArgs -contains "--basetemp" -or $PytestArgs -match '^--basetemp=')) {
    throw "Do not pass --basetemp; the PackLab wrapper owns the unique run directory."
}

if (-not $ContractTestMode) {
    & $hygiene -Mode preflight -JsonSummaryPath (Join-Path $summaryRoot "$runId-preflight.json")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
New-Item -ItemType Directory -Path $summaryRoot -Force | Out-Null
@{ schema = "packlab.pytest-run-owner.v1"; run_id = $runId; process_id = $PID; created_utc = [DateTime]::UtcNow.ToString("o") } |
    ConvertTo-Json -Compress | Set-Content -LiteralPath $ownerPath -Encoding utf8
Write-Output "packlab_run_id=$runId"
Write-Output "packlab_run_root=$runRoot"

try {
    if ($ContractTestMode) {
        $arguments = @($contractChild, $ContractScenario, $baseTemp, $contractStagingRoot, (Join-Path $runRoot "child-pids.txt"))
        if ($ContractInjectMeasurementFailure) { $arguments += "--inject-measurement-failure" }
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $ContractPython
        $psi.Arguments = (($arguments | ForEach-Object { ConvertTo-WindowsArgument ([string]$_) }) -join ' ')
    } else {
        $uv = Get-Command uv -ErrorAction Stop
        $arguments = @("run", "--locked", "pytest") + $PytestArgs + @("--basetemp", $baseTemp)
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $uv.Source
        $psi.Arguments = (($arguments | ForEach-Object { ConvertTo-WindowsArgument ([string]$_) }) -join ' ')
    }
    $psi.WorkingDirectory = $repoRoot
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $proc = [System.Diagnostics.Process]::new()
    $proc.StartInfo = $psi
    if (-not $proc.Start()) { throw "Could not start test process." }
    $stdoutTask = $proc.StandardOutput.ReadLineAsync()
    $stderrTask = $proc.StandardError.ReadLineAsync()
    $snapshot = Get-DiskSnapshot
    $peakTempBytes = $snapshot.BaseTempBytes
    $peakFixtureBytes = $snapshot.LargestFixtureBytes
    $peakFixturePath = $snapshot.LargestFixturePath
    $peakDisposableBytes = $snapshot.DisposableBytes
    $diskFreeBeforeBytes = $snapshot.DiskFreeBytes
    if ($snapshot.DisposableBytes -gt $maxDisposableBytes) {
        throw "PACKLAB_DISPOSABLE_DISK_BUDGET_EXCEEDED before_start_bytes=$($snapshot.DisposableBytes) maximum_bytes=$maxDisposableBytes"
    }
    if (-not $ContractTestMode -and $snapshot.DiskFreeBytes -lt $minimumFreeBytes) {
        throw "PACKLAB_FREE_SPACE_BUDGET_EXCEEDED disk_free_bytes=$($snapshot.DiskFreeBytes) minimum_bytes=$minimumFreeBytes"
    }

    while (-not $proc.HasExited -or $stdoutTask -or $stderrTask) {
        $tasks = @($stdoutTask, $stderrTask) | Where-Object { $null -ne $_ }
        if ($tasks.Count -gt 0) {
            [void][System.Threading.Tasks.Task]::WaitAny([System.Threading.Tasks.Task[]]$tasks, $pollMilliseconds)
        } else {
            Start-Sleep -Milliseconds $pollMilliseconds
        }
        if ($stdoutTask -and $stdoutTask.IsCompleted) {
            $line = $stdoutTask.GetAwaiter().GetResult()
            if ($null -eq $line) { $stdoutTask = $null } else { Add-OutputLine $line; $stdoutTask = $proc.StandardOutput.ReadLineAsync() }
        }
        if ($stderrTask -and $stderrTask.IsCompleted) {
            $line = $stderrTask.GetAwaiter().GetResult()
            if ($null -eq $line) { $stderrTask = $null } else { Add-OutputLine $line; $stderrTask = $proc.StandardError.ReadLineAsync() }
        }

        try { $snapshot = Get-DiskSnapshot }
        catch {
            $quotaTriggered = $true
            $exitCode = 45
            $quotaMessage = "PACKLAB_DISPOSABLE_MEASUREMENT_FAILED reason=$($_.Exception.Message)"
            Write-Output $quotaMessage
            Stop-PytestTree
            break
        }
        if ($snapshot.BaseTempBytes -gt $peakTempBytes) { $peakTempBytes = $snapshot.BaseTempBytes }
        if ($snapshot.LargestFixtureBytes -gt $peakFixtureBytes) { $peakFixtureBytes = $snapshot.LargestFixtureBytes; $peakFixturePath = $snapshot.LargestFixturePath }
        if ($snapshot.DisposableBytes -gt $peakDisposableBytes) { $peakDisposableBytes = $snapshot.DisposableBytes }
        if (-not $ContractTestMode -and $snapshot.DiskFreeBytes -lt $minimumFreeBytes) {
            $quotaTriggered = $true
            $exitCode = 46
            $quotaMessage = "PACKLAB_FREE_SPACE_BUDGET_EXCEEDED disk_free_bytes=$($snapshot.DiskFreeBytes) minimum_bytes=$minimumFreeBytes"
        } elseif ($snapshot.BaseTempBytes -gt $maxBaseTempBytes) {
            $quotaTriggered = $true
            $exitCode = 42
            $quotaMessage = "PYTEST_DISK_BUDGET_EXCEEDED basetemp_bytes=$($snapshot.BaseTempBytes) maximum_bytes=$maxBaseTempBytes"
        } elseif ($snapshot.LargestFixtureBytes -gt $maxFixtureBytes) {
            $quotaTriggered = $true
            $exitCode = 43
            $quotaMessage = "TEST_FIXTURE_DISK_BUDGET_EXCEEDED fixture_path=$($snapshot.LargestFixturePath) fixture_bytes=$($snapshot.LargestFixtureBytes) maximum_bytes=$maxFixtureBytes"
        } elseif ($snapshot.DisposableBytes -gt $maxDisposableBytes) {
            $quotaTriggered = $true
            $exitCode = 44
            $quotaMessage = "PACKLAB_DISPOSABLE_DISK_BUDGET_EXCEEDED disposable_bytes=$($snapshot.DisposableBytes) maximum_bytes=$maxDisposableBytes"
        }
        if ($quotaTriggered) {
            Write-Output $quotaMessage
            if (-not $ContractTestMode) { Show-LargestTempEntries $baseTemp }
            Stop-PytestTree
            break
        }
    }

    if (-not $quotaTriggered) {
        $snapshot = Get-DiskSnapshot
        if ($snapshot.BaseTempBytes -gt $peakTempBytes) { $peakTempBytes = $snapshot.BaseTempBytes }
        if ($snapshot.LargestFixtureBytes -gt $peakFixtureBytes) { $peakFixtureBytes = $snapshot.LargestFixtureBytes; $peakFixturePath = $snapshot.LargestFixturePath }
        if ($snapshot.DisposableBytes -gt $peakDisposableBytes) { $peakDisposableBytes = $snapshot.DisposableBytes }
        if (-not $ContractTestMode -and $snapshot.DiskFreeBytes -lt $minimumFreeBytes) {
            $quotaTriggered = $true
            $exitCode = 46
            $quotaMessage = "PACKLAB_FREE_SPACE_BUDGET_EXCEEDED disk_free_bytes=$($snapshot.DiskFreeBytes) minimum_bytes=$minimumFreeBytes"
        } elseif ($snapshot.BaseTempBytes -gt $maxBaseTempBytes) {
            $quotaTriggered = $true
            $exitCode = 42
            $quotaMessage = "PYTEST_DISK_BUDGET_EXCEEDED basetemp_bytes=$($snapshot.BaseTempBytes) maximum_bytes=$maxBaseTempBytes"
        } elseif ($snapshot.LargestFixtureBytes -gt $maxFixtureBytes) {
            $quotaTriggered = $true
            $exitCode = 43
            $quotaMessage = "TEST_FIXTURE_DISK_BUDGET_EXCEEDED fixture_path=$($snapshot.LargestFixturePath) fixture_bytes=$($snapshot.LargestFixtureBytes) maximum_bytes=$maxFixtureBytes"
        } elseif ($snapshot.DisposableBytes -gt $maxDisposableBytes) {
            $quotaTriggered = $true
            $exitCode = 44
            $quotaMessage = "PACKLAB_DISPOSABLE_DISK_BUDGET_EXCEEDED disposable_bytes=$($snapshot.DisposableBytes) maximum_bytes=$maxDisposableBytes"
        } else {
            $exitCode = $proc.ExitCode
        }
        if ($quotaTriggered) { Write-Output $quotaMessage }
    }

    if ($exitCode -ne 0 -or $quotaTriggered) {
        New-Item -ItemType Directory -Path $diagnosticsRoot -Force | Out-Null
        if ($quotaTriggered) { $tail.Enqueue($quotaMessage) }
        $tail | Set-Content -LiteralPath $diagnosticsPath -Encoding utf8
    }
} catch {
    $message = [string]$_.Exception.Message
    Add-OutputLine $message
    if ($message -like "PACKLAB_DISPOSABLE_MEASUREMENT_*") {
        $quotaTriggered = $true
        $quotaMessage = "PACKLAB_DISPOSABLE_MEASUREMENT_FAILED reason=$message"
        $exitCode = 45
    } elseif ($message -like "PYTEST_DISK_BUDGET_EXCEEDED*") {
        $quotaTriggered = $true
        $quotaMessage = $message
        $exitCode = 42
    } elseif ($message -like "TEST_FIXTURE_DISK_BUDGET_EXCEEDED*") {
        $quotaTriggered = $true
        $quotaMessage = $message
        $exitCode = 43
    } elseif ($message -like "PACKLAB_DISPOSABLE_DISK_BUDGET_EXCEEDED*") {
        $quotaTriggered = $true
        $quotaMessage = $message
        $exitCode = 44
    } elseif ($message -like "PACKLAB_FREE_SPACE_BUDGET_EXCEEDED*") {
        $quotaTriggered = $true
        $quotaMessage = $message
        $exitCode = 46
    }
    if ($proc -and -not $proc.HasExited) { Stop-PytestTree }
    if (-not $ContractTestMode) {
        New-Item -ItemType Directory -Path $diagnosticsRoot -Force | Out-Null
        $tail | Set-Content -LiteralPath $diagnosticsPath -Encoding utf8
    }
} finally {
    if ($proc -and -not $proc.HasExited) {
        try { Stop-PytestTree } catch { try { $proc.Kill() } catch { } }
    }
    Write-Output "pytest_peak_bytes=$peakTempBytes"
    Write-Output "fixture_peak_bytes=$peakFixtureBytes"
    Write-Output "fixture_peak_path=$peakFixturePath"
    Write-Output "packlab_disposable_peak_bytes=$peakDisposableBytes"
    Write-Output "disk_free_before_bytes=$diskFreeBeforeBytes"
    if ($ContractTestMode) {
        $pidRecordPath = Join-Path $runRoot "child-pids.txt"
        if (Test-Path -LiteralPath $pidRecordPath -PathType Leaf) {
            $recordedPids = @(Get-Content -LiteralPath $pidRecordPath | Where-Object { $_ -match '^\d+$' })
            if ($recordedPids.Count -gt 0) { Write-Output "contract_child_process_ids=$($recordedPids -join ',')" }
        }
        if ((Test-Path -LiteralPath $ownerPath -PathType Leaf) -and (Get-Content -LiteralPath $ownerPath -Raw | ConvertFrom-Json).schema -eq "packlab.pytest-run-owner.v1") {
            Remove-Item -LiteralPath $runRoot -Recurse -Force
        }
    } else {
        if (Test-Path -LiteralPath $ownerPath -PathType Leaf) {
            @{ schema = "packlab.pytest-run-owner.v1"; run_id = $runId; process_id = 0; created_utc = [DateTime]::UtcNow.ToString("o") } |
                ConvertTo-Json -Compress | Set-Content -LiteralPath $ownerPath -Encoding utf8
        }
        & $hygiene -Mode post-test -RunTempPath $runRoot -Apply -JsonSummaryPath $summaryPath -ObservedPytestPeakBytes $peakTempBytes -ObservedFixturePeakBytes $peakFixtureBytes -ObservedFixturePeakPath $peakFixturePath -ObservedDisposablePeakBytes $peakDisposableBytes
        if ($LASTEXITCODE -ne 0 -and $exitCode -eq 0) { $exitCode = $LASTEXITCODE }
    }
}

exit $exitCode
