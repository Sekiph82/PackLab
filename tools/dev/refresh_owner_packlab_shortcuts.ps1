[CmdletBinding()]
param([string]$OwnerRoot = (Join-Path $env:LOCALAPPDATA 'PackLab\OwnerDev'), [Parameter(Mandatory=$true)][string]$RuntimeId)

$ErrorActionPreference = 'Stop'

function Get-Sha256([string]$Path) {
    $algorithm = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try { return [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose(); $algorithm.Dispose() }
}

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class PackLabOwnerExeRefreshShell {
    [DllImport("shell32.dll", CharSet = CharSet.Unicode, EntryPoint = "ExtractIconExW", SetLastError = true)]
    public static extern uint ExtractIconEx(string file, int index, out IntPtr large, out IntPtr small, uint count);
    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] public static extern bool DestroyIcon(IntPtr icon);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true, EntryPoint = "MoveFileExW")]
    [return: MarshalAs(UnmanagedType.Bool)] public static extern bool MoveFileEx(string existing, string replacement, int flags);
    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    public static extern void SHChangeNotify(uint eventId, uint flags, string path, IntPtr item2);
}
'@

$runtimeRoot = Join-Path (Join-Path $OwnerRoot 'releases') $RuntimeId
$manifestPath = Join-Path $runtimeRoot 'owner-dev-runtime.json'
$stableIcon = Join-Path $OwnerRoot 'branding\PackLab.ico'
$launcher = Join-Path $OwnerRoot 'launcher\PackLab.exe'
$canonicalIconHash = 'a4a655fc92796413130633703602885671f5b1a0773d045ebc79d6bd522c7fc1'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$sha = [string]$manifest.source_commit
if ($sha -notmatch '^[0-9a-f]{40}$' -or $manifest.runtime_id -ne $RuntimeId -or $manifest.smoke_status -ne 'PASS') { throw 'Runtime release manifest is not valid.' }
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) { throw 'Stable native owner launcher is missing.' }
if (-not (Test-Path -LiteralPath $stableIcon -PathType Leaf) -or (Get-Sha256 $stableIcon) -ne $canonicalIconHash) { throw 'Stable canonical ICO verification failed.' }

$desktop = if ($env:PACKLAB_OWNERDEV_DESKTOP_OVERRIDE) { $env:PACKLAB_OWNERDEV_DESKTOP_OVERRIDE } else { [Environment]::GetFolderPath('DesktopDirectory') }
$programs = if ($env:PACKLAB_OWNERDEV_PROGRAMS_OVERRIDE) { $env:PACKLAB_OWNERDEV_PROGRAMS_OVERRIDE } else { [Environment]::GetFolderPath('Programs') }
if ([string]::IsNullOrWhiteSpace($desktop) -or [string]::IsNullOrWhiteSpace($programs)) { throw 'Windows Desktop or Start Menu known folder is unavailable.' }
New-Item -ItemType Directory -Force -Path $desktop, (Join-Path $programs 'PackLab') | Out-Null
$desktopExe = Join-Path $desktop 'PackLab.exe'
$obsoleteDesktopShortcut = Join-Path $desktop 'PackLab.lnk'
$temporaryDesktopExe = Join-Path $desktop ('.PackLab-' + [guid]::NewGuid().ToString('N') + '.exe')
Copy-Item -LiteralPath $launcher -Destination $temporaryDesktopExe
if ((Get-Sha256 $temporaryDesktopExe) -ne (Get-Sha256 $launcher)) { Remove-Item -LiteralPath $temporaryDesktopExe -Force; throw 'Temporary Desktop EXE differs from the stable launcher.' }
$flags = 0x1 -bor 0x8 # MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH
if (-not [PackLabOwnerExeRefreshShell]::MoveFileEx($temporaryDesktopExe, $desktopExe, $flags)) {
    Remove-Item -LiteralPath $temporaryDesktopExe -Force -ErrorAction SilentlyContinue
    throw "Could not atomically deploy Desktop PackLab.exe: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
}

# Only after the verified EXE is in place may the exact obsolete owner-created shortcut be removed.
if ((Get-Sha256 $desktopExe) -ne (Get-Sha256 $launcher)) { throw 'Actual Desktop EXE differs from the stable launcher.' }
$large = [IntPtr]::Zero
$small = [IntPtr]::Zero
$iconCount = [PackLabOwnerExeRefreshShell]::ExtractIconEx($desktopExe, 0, [ref]$large, [ref]$small, 1)
try {
    if ($iconCount -lt 1 -or ($large -eq [IntPtr]::Zero -and $small -eq [IntPtr]::Zero)) { throw 'Windows Shell could not extract an icon from actual Desktop PackLab.exe.' }
} finally {
    if ($large -ne [IntPtr]::Zero) { [void][PackLabOwnerExeRefreshShell]::DestroyIcon($large) }
    if ($small -ne [IntPtr]::Zero) { [void][PackLabOwnerExeRefreshShell]::DestroyIcon($small) }
}
if (Test-Path -LiteralPath $obsoleteDesktopShortcut -PathType Leaf) { Remove-Item -LiteralPath $obsoleteDesktopShortcut -Force }

$startMenuPath = Join-Path $programs 'PackLab\PackLab.lnk'
$shell = New-Object -ComObject WScript.Shell
if (Test-Path -LiteralPath $startMenuPath -PathType Leaf) { Remove-Item -LiteralPath $startMenuPath -Force }
$shortcut = $shell.CreateShortcut($startMenuPath)
$shortcut.TargetPath = $launcher
$shortcut.WorkingDirectory = $runtimeRoot
$shortcut.IconLocation = "$launcher,0"
$shortcut.Description = "PackLab Studio OWNER DEV $($sha.Substring(0, 8))"
$shortcut.Save()
$verify = $shell.CreateShortcut($startMenuPath)
if ([IO.Path]::GetFullPath($verify.TargetPath) -ne [IO.Path]::GetFullPath($launcher) -or $verify.Arguments) { throw 'Start Menu entry does not target the native launcher directly.' }
if (-not (Test-Path -LiteralPath $verify.TargetPath -PathType Leaf)) { throw 'Start Menu native launcher target is missing.' }
if ($verify.IconLocation -notmatch '^(.+?),0$' -or [IO.Path]::GetFullPath($Matches[1]) -ne [IO.Path]::GetFullPath($launcher)) { throw 'Start Menu icon does not use the native launcher EXE.' }
[PackLabOwnerExeRefreshShell]::SHChangeNotify(0x00002000, 0x0005, $desktopExe, [IntPtr]::Zero)
[PackLabOwnerExeRefreshShell]::SHChangeNotify(0x00002000, 0x0005, $startMenuPath, [IntPtr]::Zero)
if (Test-Path -LiteralPath $obsoleteDesktopShortcut) { throw 'Obsolete Desktop PackLab.lnk remains after native EXE deployment.' }

$launcherHash = Get-Sha256 $launcher
$desktopHash = Get-Sha256 $desktopExe
$launcherLength = (Get-Item -LiteralPath $launcher).Length
$desktopLength = (Get-Item -LiteralPath $desktopExe).Length
Write-Output "OWNER_DEV_EXE_READY $sha $RuntimeId $desktopExe $launcher $launcherHash $launcherLength $desktopHash $desktopLength"
