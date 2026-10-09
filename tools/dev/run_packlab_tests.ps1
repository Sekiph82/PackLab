[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs = @()
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$hygiene = Join-Path $PSScriptRoot "packlab_disk_hygiene.ps1"
$tempRoot = Join-Path $env:TEMP "PackLab\pytest"
$runId = "run-{0}-{1}" -f (Get-Date -Format "yyyyMMdd'T'HHmmss"), ([guid]::NewGuid().ToString("N").Substring(0, 8))
$runRoot = Join-Path $tempRoot $runId
$baseTemp = Join-Path $runRoot "pytest"
$diagnosticsRoot = Join-Path $repoRoot "reports\_local\pytest"
$diagnosticsPath = Join-Path $diagnosticsRoot "$runId.txt"
$summaryRoot = Join-Path $repoRoot "reports\_local\disk-hygiene"
$summaryPath = Join-Path $summaryRoot "$runId.json"
$maxBaseTempBytes = 4GB
$maxFixtureBytes = 2GB
$exitCode = 1
$quotaTriggered = $false
$quotaMessage = ""
$peakTempBytes = [long]0
$peakDisposableBytes = [long]0
$peakFixturePath = ""
$proc = $null
$tail = [System.Collections.Generic.Queue[string]]::new()

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

function Add-OutputLine([string]$Line) {
    if ($null -eq $Line) { return }
    Write-Output $Line
    $tail.Enqueue($Line)
    while ($tail.Count -gt 200) { [void]$tail.Dequeue() }
}

function Get-TempTreeBytes([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return [long]0 }
    $total = [long]0
    foreach ($file in Get-ChildItem -LiteralPath $Path -File -Force -Recurse -ErrorAction SilentlyContinue) {
        $total += [long]$file.Length
    }
    return $total
}

function Get-TempTreeStats([string]$Path) {
    $total = [long]0
    $fixtureSizes = @{}
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        return [pscustomobject]@{ TotalBytes = $total; LargestFixtureBytes = [long]0; LargestFixturePath = "" }
    }
    $prefix = (Resolve-Path -LiteralPath $Path).Path.TrimEnd('\') + '\'
    foreach ($file in Get-ChildItem -LiteralPath $Path -File -Force -Recurse -ErrorAction SilentlyContinue) {
        $length = [long]$file.Length
        $total += $length
        $relative = $file.FullName.Substring($prefix.Length)
        $parts = $relative -split '[\\/]'
        $fixtureKey = if ($parts.Count -gt 1 -and $parts[0] -match '^pytest-') { Join-Path $parts[0] $parts[1] } else { $parts[0] }
        $fixtureSizes[$fixtureKey] = [long]$fixtureSizes[$fixtureKey] + $length
    }
    $largest = $fixtureSizes.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 1
    return [pscustomobject]@{
        TotalBytes = $total
        LargestFixtureBytes = [long]$(if ($largest) { $largest.Value } else { 0 })
        LargestFixturePath = [string]$(if ($largest) { $largest.Key } else { "" })
    }
}

function Get-FixedPackLabDisposableBytes {
    $roots = @(
        (Join-Path $repoRoot "build"),
        (Join-Path $repoRoot "dist"),
        (Join-Path $repoRoot "staging"),
        (Join-Path $repoRoot "reports\_local\pytest")
    )
    $total = [long]0
    foreach ($path in $roots) { $total += Get-TempTreeBytes $path }
    return $total
}

function Show-LargestTempEntries([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return }
    $fileSizes = @{}
    $directorySizes = @{}
    $prefix = (Resolve-Path -LiteralPath $Path).Path.TrimEnd('\') + '\'
    foreach ($file in Get-ChildItem -LiteralPath $Path -File -Force -Recurse -ErrorAction SilentlyContinue) {
        $fileSizes[$file.FullName] = [long]$file.Length
        $relative = $file.FullName.Substring($prefix.Length)
        $first = ($relative -split '[\\/]')[0]
        $directorySizes[$first] = [long]$directorySizes[$first] + [long]$file.Length
    }
    foreach ($entry in ($directorySizes.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 10)) {
        Write-Output "largest_temp_directory=$($entry.Value) $($entry.Key)"
    }
    foreach ($entry in ($fileSizes.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 10)) {
        Write-Output "largest_temp_file=$($entry.Value) $($entry.Key)"
    }
}

if ($PytestArgs -contains "--basetemp" -or $PytestArgs -match '^--basetemp=') {
    throw "Do not pass --basetemp; the PackLab wrapper owns the unique run directory."
}

& $hygiene -Mode preflight -JsonSummaryPath (Join-Path $summaryRoot "$runId-preflight.json")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
New-Item -ItemType Directory -Path $summaryRoot -Force | Out-Null
$fixedDisposableBytes = Get-FixedPackLabDisposableBytes
@{ schema = "packlab.pytest-run-owner.v1"; run_id = $runId; process_id = $PID; created_utc = [DateTime]::UtcNow.ToString("o") } |
    ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $runRoot ".packlab-run.json") -Encoding utf8

try {
    $uv = Get-Command uv -ErrorAction Stop
    $arguments = @("run", "--locked", "pytest") + $PytestArgs + @("--basetemp", $baseTemp)
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $uv.Source
    $psi.Arguments = (($arguments | ForEach-Object { ConvertTo-WindowsArgument ([string]$_) }) -join ' ')
    $psi.WorkingDirectory = $repoRoot
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $proc = [System.Diagnostics.Process]::new()
    $proc.StartInfo = $psi
    if (-not $proc.Start()) { throw "Could not start uv pytest process." }
    $stdoutTask = $proc.StandardOutput.ReadLineAsync()
    $stderrTask = $proc.StandardError.ReadLineAsync()
    $initialStats = Get-TempTreeStats $baseTemp
    $peakTempBytes = $initialStats.TotalBytes
    $peakFixtureBytes = $initialStats.LargestFixtureBytes
    $peakFixturePath = $initialStats.LargestFixturePath
    $peakDisposableBytes = $fixedDisposableBytes + (Get-TempTreeBytes $tempRoot)

    while (-not $proc.HasExited) {
        [void][System.Threading.Tasks.Task]::WaitAny([System.Threading.Tasks.Task[]]@($stdoutTask, $stderrTask), 500)
        if ($stdoutTask -and $stdoutTask.IsCompleted) {
            $line = $stdoutTask.GetAwaiter().GetResult()
            if ($null -eq $line) { $stdoutTask = $null } else { Add-OutputLine $line; $stdoutTask = $proc.StandardOutput.ReadLineAsync() }
        }
        if ($stderrTask -and $stderrTask.IsCompleted) {
            $line = $stderrTask.GetAwaiter().GetResult()
            if ($null -eq $line) { $stderrTask = $null } else { Add-OutputLine $line; $stderrTask = $proc.StandardError.ReadLineAsync() }
        }
        $stats = Get-TempTreeStats $baseTemp
        $currentBytes = $stats.TotalBytes
        if ($currentBytes -gt $peakTempBytes) { $peakTempBytes = $currentBytes }
        if ($stats.LargestFixtureBytes -gt $peakFixtureBytes) { $peakFixtureBytes = $stats.LargestFixtureBytes; $peakFixturePath = $stats.LargestFixturePath }
        $disposableBytes = $fixedDisposableBytes + (Get-TempTreeBytes $tempRoot)
        if ($disposableBytes -gt $peakDisposableBytes) { $peakDisposableBytes = $disposableBytes }
        if ($currentBytes -gt $maxBaseTempBytes) {
            $quotaTriggered = $true
            $exitCode = 42
            $quotaMessage = "PYTEST_DISK_BUDGET_EXCEEDED basetemp_bytes=$currentBytes maximum_bytes=$maxBaseTempBytes"
            Write-Output $quotaMessage
            & taskkill.exe /PID $proc.Id /T /F 2>&1 | ForEach-Object { Write-Output $_ }
            try { if (-not $proc.HasExited) { $proc.Kill() } } catch { }
            break
        }
        if ($stats.LargestFixtureBytes -gt $maxFixtureBytes) {
            $quotaTriggered = $true
            $exitCode = 43
            $quotaMessage = "TEST_FIXTURE_DISK_BUDGET_EXCEEDED fixture_path=$($stats.LargestFixturePath) fixture_bytes=$($stats.LargestFixtureBytes) maximum_bytes=$maxFixtureBytes"
            Write-Output $quotaMessage
            & taskkill.exe /PID $proc.Id /T /F 2>&1 | ForEach-Object { Write-Output $_ }
            try { if (-not $proc.HasExited) { $proc.Kill() } } catch { }
            break
        }
    }

    if (-not $quotaTriggered) {
        $proc.WaitForExit()
        $finalStats = Get-TempTreeStats $baseTemp
        $finalTempBytes = $finalStats.TotalBytes
        if ($finalTempBytes -gt $peakTempBytes) { $peakTempBytes = $finalTempBytes }
        if ($finalStats.LargestFixtureBytes -gt $peakFixtureBytes) { $peakFixtureBytes = $finalStats.LargestFixtureBytes; $peakFixturePath = $finalStats.LargestFixturePath }
        $finalDisposableBytes = $fixedDisposableBytes + (Get-TempTreeBytes $tempRoot)
        if ($finalDisposableBytes -gt $peakDisposableBytes) { $peakDisposableBytes = $finalDisposableBytes }
        if ($peakTempBytes -gt $maxBaseTempBytes) {
            $quotaTriggered = $true
            $exitCode = 42
            $quotaMessage = "PYTEST_DISK_BUDGET_EXCEEDED basetemp_bytes=$peakTempBytes maximum_bytes=$maxBaseTempBytes"
            Write-Output $quotaMessage
            Show-LargestTempEntries $baseTemp
        }
        if ($peakFixtureBytes -gt $maxFixtureBytes) {
            $quotaTriggered = $true
            $exitCode = 43
            $quotaMessage = "TEST_FIXTURE_DISK_BUDGET_EXCEEDED fixture_path=$peakFixturePath fixture_bytes=$peakFixtureBytes maximum_bytes=$maxFixtureBytes"
            Write-Output $quotaMessage
            Show-LargestTempEntries $baseTemp
        }
        while ($stdoutTask -or $stderrTask) {
            $tasks = @($stdoutTask, $stderrTask) | Where-Object { $null -ne $_ }
            if ($tasks.Count -eq 0) { break }
            [void][System.Threading.Tasks.Task]::WaitAny([System.Threading.Tasks.Task[]]$tasks, 500)
            if ($stdoutTask -and $stdoutTask.IsCompleted) {
                $line = $stdoutTask.GetAwaiter().GetResult()
                if ($null -eq $line) { $stdoutTask = $null } else { Add-OutputLine $line; $stdoutTask = $proc.StandardOutput.ReadLineAsync() }
            }
            if ($stderrTask -and $stderrTask.IsCompleted) {
                $line = $stderrTask.GetAwaiter().GetResult()
                if ($null -eq $line) { $stderrTask = $null } else { Add-OutputLine $line; $stderrTask = $proc.StandardError.ReadLineAsync() }
            }
        }
        if (-not $quotaTriggered) { $exitCode = $proc.ExitCode }
    } else {
        Start-Sleep -Milliseconds 500
        Show-LargestTempEntries $baseTemp
    }

    if ($exitCode -ne 0 -or $quotaTriggered) {
        New-Item -ItemType Directory -Path $diagnosticsRoot -Force | Out-Null
        if ($quotaTriggered) { $tail.Enqueue($quotaMessage) }
        $tail | Set-Content -LiteralPath $diagnosticsPath -Encoding utf8
    }
} catch {
    Add-OutputLine $_.Exception.ToString()
    New-Item -ItemType Directory -Path $diagnosticsRoot -Force | Out-Null
    $tail | Set-Content -LiteralPath $diagnosticsPath -Encoding utf8
    $exitCode = 1
} finally {
    if ($proc -and -not $proc.HasExited) {
        try { & taskkill.exe /PID $proc.Id /T /F | Out-Null } catch { try { $proc.Kill() } catch { } }
    }
    $ownerPath = Join-Path $runRoot ".packlab-run.json"
    if (Test-Path -LiteralPath $ownerPath -PathType Leaf) {
        @{ schema = "packlab.pytest-run-owner.v1"; run_id = $runId; process_id = 0; created_utc = [DateTime]::UtcNow.ToString("o") } |
            ConvertTo-Json -Compress | Set-Content -LiteralPath $ownerPath -Encoding utf8
    }
    & $hygiene -Mode post-test -RunTempPath $runRoot -Apply -JsonSummaryPath $summaryPath -ObservedPytestPeakBytes $peakTempBytes -ObservedFixturePeakBytes $peakFixtureBytes -ObservedFixturePeakPath $peakFixturePath -ObservedDisposablePeakBytes $peakDisposableBytes
    if ($LASTEXITCODE -ne 0 -and $exitCode -eq 0) { $exitCode = $LASTEXITCODE }
    if ($quotaTriggered -and $exitCode -eq 0) { $exitCode = 42 }
}

exit $exitCode
