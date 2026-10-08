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
& (Join-Path $PSScriptRoot 'update_owner_dev_runtime.ps1') @deployArgs
if ($LASTEXITCODE -ne 0) { throw 'Owner runtime deployment failed.' }
$ownerRoot = Join-Path $env:LOCALAPPDATA 'PackLab\OwnerDev'
& (Join-Path $PSScriptRoot 'build_owner_packlab_exe.ps1') -RepositoryRoot $root -OwnerRoot $ownerRoot
if ($LASTEXITCODE -ne 0) { throw 'Native owner launcher build/deployment failed.' }
$refreshOutput = & (Join-Path $PSScriptRoot 'refresh_owner_packlab_shortcuts.ps1') -OwnerRoot $ownerRoot
if ($LASTEXITCODE -ne 0) { throw 'Desktop EXE deployment or Start Menu refresh failed.' }
$manifest = Get-Content -LiteralPath (Join-Path $ownerRoot 'current\owner-dev-runtime.json') -Raw | ConvertFrom-Json
$expectedSha = (& git -C $root rev-parse HEAD).Trim()
if ($manifest.source_commit -ne $expectedSha) { throw 'Runtime SHA differs from refreshed source HEAD.' }
if ($refreshOutput -notmatch ('OWNER_DEV_EXE_READY ' + [regex]::Escape($expectedSha) + ' ')) { throw 'Native Desktop owner readiness proof is missing.' }
Write-Output $refreshOutput
