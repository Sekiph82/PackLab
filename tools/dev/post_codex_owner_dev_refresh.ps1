[CmdletBinding()]
param([switch]$AllowPublishedCommit)

$ErrorActionPreference = 'Stop'
$root = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
if ($AllowPublishedCommit) {
    & git -C $root fetch origin main
    if ($LASTEXITCODE -ne 0) { throw 'Could not refresh origin/main before owner runtime deployment.' }
    $localSha = (& git -C $root rev-parse HEAD).Trim()
    $remoteSha = (& git -C $root rev-parse origin/main).Trim()
    if ($localSha -ne $remoteSha) { throw 'Local HEAD does not equal fetched origin/main.' }
}
$deployArgs = @{ RepositoryRoot = $root }
if ($AllowPublishedCommit) { $deployArgs.AllowPublishedCommit = $true }
$runtimeOutput = @(& (Join-Path $PSScriptRoot 'update_owner_dev_runtime.ps1') @deployArgs)
if ($LASTEXITCODE -ne 0) { throw 'Owner runtime deployment failed.' }
$runtimeLine = $runtimeOutput | Where-Object { $_ -match '^OWNER_DEV_RUNTIME_READY ' } | Select-Object -Last 1
if (-not $runtimeLine -or $runtimeLine -notmatch '^OWNER_DEV_RUNTIME_READY ([0-9a-f]{40}) ([0-9a-f]{40}-[0-9a-f]{32}) ') { throw 'Owner runtime release identity is missing.' }
$runtimeSha = $Matches[1]
$runtimeId = $Matches[2]
if ($runtimeSha -ne $sha) { throw 'Owner runtime release differs from source HEAD.' }
$ownerRoot = Join-Path $env:LOCALAPPDATA 'PackLab\OwnerDev'
& (Join-Path $PSScriptRoot 'build_owner_packlab_exe.ps1') -RepositoryRoot $root -OwnerRoot $ownerRoot -SourceCommit $sha -RuntimeId $runtimeId
if ($LASTEXITCODE -ne 0) { throw 'Native owner launcher build/deployment failed.' }
$refreshOutput = & (Join-Path $PSScriptRoot 'refresh_owner_packlab_shortcuts.ps1') -OwnerRoot $ownerRoot -RuntimeId $runtimeId
if ($LASTEXITCODE -ne 0) { throw 'Desktop EXE deployment or Start Menu refresh failed.' }
$currentOutput = & (Join-Path $PSScriptRoot 'update_owner_dev_current_junction.ps1') -OwnerRoot $ownerRoot -RuntimeId $runtimeId
if ($LASTEXITCODE -ne 0 -or $currentOutput -notmatch ('OWNER_DEV_CURRENT_READY ' + [regex]::Escape($sha) + ' ' + [regex]::Escape($runtimeId) + ' ')) { throw 'Compatibility current junction refresh failed.' }
$manifestPath = Join-Path (Join-Path $ownerRoot 'releases') (Join-Path $runtimeId 'owner-dev-runtime.json')
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$expectedSha = (& git -C $root rev-parse HEAD).Trim()
if ($manifest.source_commit -ne $expectedSha -or $manifest.runtime_id -ne $runtimeId -or $manifest.uv_lock_sha256 -notmatch '^[0-9a-f]{64}$') { throw 'Runtime/source/dependency-lock identity differs from refreshed source HEAD.' }
if ($refreshOutput -notmatch ('OWNER_DEV_EXE_READY ' + [regex]::Escape($expectedSha) + ' ' + [regex]::Escape($runtimeId) + ' ')) { throw 'Native Desktop owner readiness proof is missing.' }
Write-Output $refreshOutput
Write-Output $currentOutput
