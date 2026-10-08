[CmdletBinding()]
param(
    [string]$OwnerRoot = (Join-Path $env:LOCALAPPDATA 'PackLab\OwnerDev'),
    [Parameter(Mandatory=$true)][string]$RuntimeId
)

$ErrorActionPreference = 'Stop'
if ($RuntimeId -notmatch '^[0-9a-f]{40}-[0-9a-f]{32}$') { throw 'Runtime ID is invalid.' }
$runtimeRoot = Join-Path (Join-Path $OwnerRoot 'releases') $RuntimeId
$manifestPath = Join-Path $runtimeRoot 'owner-dev-runtime.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.runtime_id -ne $RuntimeId -or $manifest.source_commit -notmatch '^[0-9a-f]{40}$' -or $manifest.smoke_status -ne 'PASS') {
    throw 'Target runtime release is not complete and smoke-verified.'
}
$visibleStudio = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq 'PackLab Studio' })
if ($visibleStudio.Count -gt 0) { throw 'A PackLab Studio window is running; refusing to switch the compatibility runtime path.' }
$currentPrefix = (Join-Path $OwnerRoot 'current') + '\'
$activeCurrentProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -and $_.CommandLine.IndexOf($currentPrefix, [StringComparison]::OrdinalIgnoreCase) -ge 0 })
if ($activeCurrentProcesses.Count -gt 0) { throw 'An OWNER DEV process is using the compatibility current path; refusing to switch it.' }

$current = Join-Path $OwnerRoot 'current'
$currentTemp = Join-Path $OwnerRoot ('current-' + [guid]::NewGuid().ToString('N'))
$previousCurrent = $null
$previousTarget = $null
if (Test-Path -LiteralPath $current) {
    $currentItem = Get-Item -LiteralPath $current -Force
    if (($currentItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        $previousManifest = Get-Content -LiteralPath (Join-Path $current 'owner-dev-runtime.json') -Raw | ConvertFrom-Json
        if ([string]$previousManifest.runtime_id -notmatch '^[0-9a-f]{40}-[0-9a-f]{32}$') { throw 'Current junction has an invalid prior runtime identity.' }
        $previousTarget = Join-Path (Join-Path $OwnerRoot 'releases') ([string]$previousManifest.runtime_id)
        [IO.Directory]::Delete($current, $false)
    } else {
        $previousCurrent = Join-Path $OwnerRoot ('previous-' + [guid]::NewGuid().ToString('N'))
        Move-Item -LiteralPath $current -Destination $previousCurrent
    }
}
try {
        New-Item -ItemType Junction -Path $currentTemp -Target $runtimeRoot | Out-Null
        Move-Item -LiteralPath $currentTemp -Destination $current
    $currentTarget = [string](Get-Item -LiteralPath $current -Force).Target
    if ([IO.Path]::GetFullPath($currentTarget) -ne [IO.Path]::GetFullPath($runtimeRoot)) { throw 'Compatibility current junction does not resolve to the selected immutable release.' }
} catch {
    if (Test-Path -LiteralPath $currentTemp) { [IO.Directory]::Delete($currentTemp, $false) }
    if (-not (Test-Path -LiteralPath $current)) {
        if ($previousCurrent -and (Test-Path -LiteralPath $previousCurrent)) {
            Move-Item -LiteralPath $previousCurrent -Destination $current
        } elseif ($previousTarget -and (Test-Path -LiteralPath $previousTarget)) {
            New-Item -ItemType Junction -Path $current -Target $previousTarget | Out-Null
        }
    }
    throw
}
Write-Output "OWNER_DEV_CURRENT_READY $($manifest.source_commit) $RuntimeId $current"
