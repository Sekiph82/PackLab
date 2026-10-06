[CmdletBinding()]
param([string]$OwnerRoot = (Join-Path $env:LOCALAPPDATA 'PackLab\OwnerDev'))

$ErrorActionPreference = 'Stop'

function Get-Sha256([string]$Path) {
    $algorithm = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try { return [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose(); $algorithm.Dispose() }
}

$current = Join-Path $OwnerRoot 'current'
$manifestPath = Join-Path $current 'owner-dev-runtime.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$sha = [string]$manifest.source_commit
if ($sha -notmatch '^[0-9a-f]{40}$' -or $manifest.smoke_status -ne 'PASS') { throw 'Current runtime manifest is not valid.' }
$launcher = Join-Path $current 'tools\dev\launch_owner_packlab.ps1'
$icon = Join-Path $current 'apps\windows-studio\assets\branding\PackLab.ico'
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) { throw 'Stable owner launcher is missing.' }
if (-not (Test-Path -LiteralPath $icon -PathType Leaf)) { throw 'Canonical PackLab icon is missing.' }
$iconHash = Get-Sha256 $icon
if ($iconHash -ne $manifest.icon_sha256) { throw 'Runtime icon digest differs from its manifest.' }
$desktop = if ($env:PACKLAB_OWNERDEV_DESKTOP_OVERRIDE) { $env:PACKLAB_OWNERDEV_DESKTOP_OVERRIDE } else { [Environment]::GetFolderPath('DesktopDirectory') }
$programs = if ($env:PACKLAB_OWNERDEV_PROGRAMS_OVERRIDE) { $env:PACKLAB_OWNERDEV_PROGRAMS_OVERRIDE } else { [Environment]::GetFolderPath('Programs') }
if ([string]::IsNullOrWhiteSpace($desktop) -or [string]::IsNullOrWhiteSpace($programs)) { throw 'Windows Desktop or Start Menu known folder is unavailable.' }
$startMenuDir = Join-Path $programs 'PackLab'
New-Item -ItemType Directory -Force -Path $desktop, $startMenuDir | Out-Null
$shell = New-Object -ComObject WScript.Shell
$description = "PackLab Studio OWNER DEV $([char]0x2022) $($sha.Substring(0, 8))"
$items = @(
    @{ Path = (Join-Path $desktop 'PackLab.lnk'); StartIn = $desktop },
    @{ Path = (Join-Path $startMenuDir 'PackLab.lnk'); StartIn = $current }
)
foreach ($item in $items) {
    $shortcut = $shell.CreateShortcut($item.Path)
    $shortcut.TargetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    $shortcut.Arguments = "-NoProfile -WindowStyle Hidden -File `"$launcher`""
    $shortcut.WorkingDirectory = $item.StartIn
    $shortcut.IconLocation = "$icon,0"
    $shortcut.Description = $description
    $shortcut.Save()
    $verify = $shell.CreateShortcut($item.Path)
    if (-not (Test-Path -LiteralPath $verify.TargetPath -PathType Leaf)) { throw "Shortcut target missing: $($item.Path)" }
    if (-not $verify.Arguments.Contains($launcher) -or -not $verify.Arguments.Contains('launch_owner_packlab.ps1')) { throw "Shortcut arguments invalid: $($item.Path)" }
    if (-not $verify.IconLocation.StartsWith($icon, [StringComparison]::OrdinalIgnoreCase)) { throw "Shortcut icon invalid: $($item.Path)" }
    if ($verify.Description -ne $description) { throw "Shortcut description does not match deployed SHA: $($item.Path)" }
}
Write-Output "OWNER_DEV_SHORTCUTS_REFRESHED $sha $($items[0].Path) $($items[1].Path) $iconHash"
