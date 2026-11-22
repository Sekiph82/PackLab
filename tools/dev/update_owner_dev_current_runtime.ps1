[CmdletBinding()]
param(
    [string]$OwnerRoot = (Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) 'PackLab\OwnerDev'),
    [Parameter(Mandatory=$true)][string]$RuntimeId
)

$ErrorActionPreference = 'Stop'
function Get-Sha256([string]$Path) {
    $algorithm = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try { return [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose(); $algorithm.Dispose() }
}
if ($RuntimeId -notmatch '^[0-9a-f]{40}-[0-9a-f]{32}$') { throw 'Runtime ID is invalid.' }
$runtimeRoot = Join-Path (Join-Path $OwnerRoot 'releases') $RuntimeId
$manifestPath = Join-Path $runtimeRoot 'owner-dev-runtime.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.runtime_id -ne $RuntimeId -or $manifest.source_commit -notmatch '^[0-9a-f]{40}$' -or $manifest.smoke_status -ne 'PASS') {
    throw 'Target runtime release is not complete and smoke-verified.'
}
$visibleStudio = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq 'PackLab Studio' })
if ($visibleStudio.Count -gt 0) { throw 'A PackLab Studio window is running; refusing to replace the compatibility runtime path.' }
$currentPrefix = (Join-Path $OwnerRoot 'current') + '\'
$activeCurrentProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -and $_.CommandLine.IndexOf($currentPrefix, [StringComparison]::OrdinalIgnoreCase) -ge 0 })
if ($activeCurrentProcesses.Count -gt 0) { throw 'An OWNER DEV process is using the compatibility current path; refusing to replace it.' }

$current = Join-Path $OwnerRoot 'current'
$stage = Join-Path $OwnerRoot ('current-stage-' + [guid]::NewGuid().ToString('N'))
$previous = $null
New-Item -ItemType Directory -Path $stage | Out-Null
try {
    Get-ChildItem -LiteralPath $runtimeRoot -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $stage -Recurse -Force
    }
    $stagedManifest = Get-Content -LiteralPath (Join-Path $stage 'owner-dev-runtime.json') -Raw | ConvertFrom-Json
    $stagedLockHash = Get-Sha256 (Join-Path $stage 'uv.lock')
    if ($stagedManifest.source_commit -ne $manifest.source_commit -or $stagedManifest.runtime_id -ne $RuntimeId -or
        $stagedManifest.uv_lock_sha256 -ne $manifest.uv_lock_sha256 -or $stagedLockHash -ne $manifest.uv_lock_sha256) {
        throw 'Staged current runtime does not match the immutable release identity.'
    }

    if (Test-Path -LiteralPath $current) {
        $currentItem = Get-Item -LiteralPath $current -Force
        if (($currentItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            [IO.Directory]::Delete($current, $false)
        } else {
            $previous = Join-Path $OwnerRoot ('previous-' + [guid]::NewGuid().ToString('N'))
            Move-Item -LiteralPath $current -Destination $previous
        }
    }
    try {
        Move-Item -LiteralPath $stage -Destination $current
    } catch {
        if (-not (Test-Path -LiteralPath $current) -and $previous -and (Test-Path -LiteralPath $previous)) {
            Move-Item -LiteralPath $previous -Destination $current
        }
        throw
    }
    $currentManifest = Get-Content -LiteralPath (Join-Path $current 'owner-dev-runtime.json') -Raw | ConvertFrom-Json
    if ($currentManifest.source_commit -ne $manifest.source_commit -or $currentManifest.runtime_id -ne $RuntimeId) {
        throw 'Promoted current runtime does not match the selected release.'
    }
} catch {
    if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
    throw
}
# Owner request (2026-11-22): keep only the newest rollback copy. Older previous-<guid>
# folders are regenerated runtime snapshots (source of a published commit + venv); a failed
# cleanup never fails the promotion.
Get-ChildItem -LiteralPath $OwnerRoot -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -cmatch '^previous-[0-9a-f]{32}$' -and (-not $previous -or $_.FullName -ne $previous) } |
    ForEach-Object {
        try { Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction Stop; Write-Output "OWNER_DEV_OLD_PREVIOUS_REMOVED $($_.Name)" }
        catch { Write-Warning "Could not remove old rollback copy $($_.Name): $($_.Exception.Message)" }
    }
# Owner request (2026-11-22): keep only the release that is now current. Releases are
# regenerated from published commits; one still used by a running process is kept.
$releasesRoot = Join-Path $OwnerRoot 'releases'
Get-ChildItem -LiteralPath $releasesRoot -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -cmatch '^[0-9a-f]{40}-[0-9a-f]{32}$' -and $_.Name -ne $RuntimeId } |
    ForEach-Object {
        $releasePrefix = $_.FullName + ''
        $inUse = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -and $_.CommandLine.IndexOf($releasePrefix, [StringComparison]::OrdinalIgnoreCase) -ge 0 })
        if ($inUse.Count -gt 0) { Write-Warning "Release $($_.Name) is in use; kept."; return }
        try { Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction Stop; Write-Output "OWNER_DEV_OLD_RELEASE_REMOVED $($_.Name)" }
        catch { Write-Warning "Could not remove old release $($_.Name): $($_.Exception.Message)" }
    }
Write-Output "OWNER_DEV_CURRENT_READY $($manifest.source_commit) $RuntimeId $current"
