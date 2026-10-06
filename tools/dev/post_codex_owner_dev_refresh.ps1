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
$refreshOutput = & (Join-Path $PSScriptRoot 'refresh_owner_packlab_shortcuts.ps1') -OwnerRoot $ownerRoot
if ($LASTEXITCODE -ne 0) { throw 'Owner shortcut refresh failed.' }
$manifest = Get-Content -LiteralPath (Join-Path $ownerRoot 'current\owner-dev-runtime.json') -Raw | ConvertFrom-Json
$desktop = if ($env:PACKLAB_OWNERDEV_DESKTOP_OVERRIDE) { Join-Path $env:PACKLAB_OWNERDEV_DESKTOP_OVERRIDE 'PackLab.lnk' } else { Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) 'PackLab.lnk' }
$programs = if ($env:PACKLAB_OWNERDEV_PROGRAMS_OVERRIDE) { Join-Path $env:PACKLAB_OWNERDEV_PROGRAMS_OVERRIDE 'PackLab\PackLab.lnk' } else { Join-Path ([Environment]::GetFolderPath('Programs')) 'PackLab\PackLab.lnk' }
if (-not (Test-Path -LiteralPath $desktop -PathType Leaf) -or -not (Test-Path -LiteralPath $programs -PathType Leaf)) { throw 'Shortcut verification failed after refresh.' }
if ($manifest.source_commit -ne (& git -C $root rev-parse HEAD).Trim()) { throw 'Runtime SHA differs from refreshed source HEAD.' }
Write-Output "OWNER_DEV_READY $($manifest.source_commit) $desktop $programs"
