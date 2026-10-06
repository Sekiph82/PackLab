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
$branding = Join-Path $OwnerRoot 'branding'
$manifestPath = Join-Path $current 'owner-dev-runtime.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$sha = [string]$manifest.source_commit
if ($sha -notmatch '^[0-9a-f]{40}$' -or $manifest.smoke_status -ne 'PASS') { throw 'Current runtime manifest is not valid.' }
$launcher = Join-Path $current 'tools\dev\launch_owner_packlab.ps1'
$runtimeIcon = Join-Path $current 'apps\windows-studio\assets\branding\PackLab.ico'
$icon = Join-Path $branding 'PackLab.ico'
$canonicalIconHash = 'a4a655fc92796413130633703602885671f5b1a0773d045ebc79d6bd522c7fc1'
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) { throw 'Stable owner launcher is missing.' }
if (-not (Test-Path -LiteralPath $runtimeIcon -PathType Leaf)) { throw 'Canonical PackLab runtime icon is missing.' }
New-Item -ItemType Directory -Force -Path $branding | Out-Null
Copy-Item -LiteralPath $runtimeIcon -Destination $icon -Force
$iconHash = Get-Sha256 $icon
if ($iconHash -ne $canonicalIconHash -or $iconHash -ne $manifest.icon_sha256) { throw 'Stable icon digest differs from the canonical icon or runtime manifest.' }
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class PackLabIconProbe {
    [DllImport("shell32.dll", CharSet = CharSet.Unicode, EntryPoint = "ExtractIconExW", SetLastError = true)]
    public static extern uint ExtractIconEx(string file, int index, out IntPtr large, out IntPtr small, uint count);
    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool DestroyIcon(IntPtr icon);
}
'@
$largeIcon = [IntPtr]::Zero
$smallIcon = [IntPtr]::Zero
$extractedCount = [PackLabIconProbe]::ExtractIconEx($icon, 0, [ref]$largeIcon, [ref]$smallIcon, 1)
if ($extractedCount -lt 1 -or ($largeIcon -eq [IntPtr]::Zero -and $smallIcon -eq [IntPtr]::Zero)) { throw 'Windows Shell could not extract a nonzero icon handle from the stable ICO.' }
if ($largeIcon -ne [IntPtr]::Zero) { [void][PackLabIconProbe]::DestroyIcon($largeIcon) }
if ($smallIcon -ne [IntPtr]::Zero) { [void][PackLabIconProbe]::DestroyIcon($smallIcon) }
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
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class PackLabShellNotify {
    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    public static extern void SHChangeNotify(uint eventId, uint flags, string path, IntPtr item2);
}
'@
foreach ($item in $items) {
    if (Test-Path -LiteralPath $item.Path -PathType Leaf) { Remove-Item -LiteralPath $item.Path -Force }
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
    if ($verify.IconLocation -notmatch '^(.+?),(\d+)$' -or [IO.Path]::GetFullPath($Matches[1]) -ne [IO.Path]::GetFullPath($icon)) { throw "Shortcut icon does not resolve to the stable branding ICO: $($item.Path)" }
    [PackLabShellNotify]::SHChangeNotify(0x00002000, 0x0005, $item.Path, [IntPtr]::Zero)
}
Write-Output "OWNER_DEV_SHORTCUTS_REFRESHED $sha $($items[0].Path) $($items[1].Path) $icon $iconHash"
