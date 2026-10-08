[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$OwnerRoot = (Join-Path $env:LOCALAPPDATA 'PackLab\OwnerDev')
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $RepositoryRoot).Path
$runtime = Join-Path $OwnerRoot 'current'
$canonicalIcon = Join-Path $runtime 'apps\windows-studio\assets\branding\PackLab.ico'
$stableIcon = Join-Path $OwnerRoot 'branding\PackLab.ico'
$source = Join-Path $root 'tools\dev\PackLabOwnerLauncher.cs'
$launcherDir = Join-Path $OwnerRoot 'launcher'
$stableExe = Join-Path $launcherDir 'PackLab.exe'
$expectedIconHash = 'a4a655fc92796413130633703602885671f5b1a0773d045ebc79d6bd522c7fc1'

function Get-Sha256([string]$Path) {
    $algorithm = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try { return [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose(); $algorithm.Dispose() }
}

function Assert-GuiExecutable([string]$Path) {
    $bytes = [IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -lt 256 -or $bytes[0] -ne 0x4d -or $bytes[1] -ne 0x5a) { throw "Not a valid PE executable: $Path" }
    $peOffset = [BitConverter]::ToInt32($bytes, 0x3c)
    if ($peOffset -lt 0 -or $peOffset + 90 -gt $bytes.Length -or [BitConverter]::ToUInt32($bytes, $peOffset) -ne 0x00004550) { throw "Invalid PE header: $Path" }
    $subsystem = [BitConverter]::ToUInt16($bytes, $peOffset + 24 + 68)
    if ($subsystem -ne 2) { throw "Launcher PE subsystem is $subsystem; expected Windows GUI (2)." }
}

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class PackLabLauncherShellProbe {
    [DllImport("shell32.dll", CharSet = CharSet.Unicode, EntryPoint = "ExtractIconExW", SetLastError = true)]
    public static extern uint ExtractIconEx(string file, int index, out IntPtr large, out IntPtr small, uint count);
    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] public static extern bool DestroyIcon(IntPtr icon);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true, EntryPoint = "MoveFileExW")]
    [return: MarshalAs(UnmanagedType.Bool)] public static extern bool MoveFileEx(string existing, string replacement, int flags);
}
'@

if (-not (Test-Path -LiteralPath $canonicalIcon -PathType Leaf)) { throw 'Canonical runtime ICO is missing.' }
if ((Get-Sha256 $canonicalIcon) -ne $expectedIconHash) { throw 'Canonical repository ICO digest does not match the frozen icon hash.' }
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw 'Checked-in native launcher source is missing.' }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $stableIcon), $launcherDir | Out-Null
Copy-Item -LiteralPath $canonicalIcon -Destination $stableIcon -Force
if ((Get-Sha256 $stableIcon) -ne $expectedIconHash) { throw 'Stable OWNER DEV ICO digest is incorrect.' }

$compiler = $null
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (Test-Path -LiteralPath $vswhere) {
    $vsRoot = (& $vswhere -latest -products '*' -requires Microsoft.Component.MSBuild -property installationPath | Select-Object -First 1)
    if ($vsRoot) {
        $candidate = Join-Path $vsRoot 'MSBuild\Current\Bin\Roslyn\csc.exe'
        if (Test-Path -LiteralPath $candidate) { $compiler = $candidate }
    }
}
if (-not $compiler) {
    $compilerCandidates = @(
        (Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'),
        (Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe')
    )
    $compiler = $compilerCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
}
if (-not $compiler) { throw 'No installed C# compiler was found; no toolchain was downloaded or installed.' }

$tempExe = Join-Path $launcherDir ('PackLab-' + [guid]::NewGuid().ToString('N') + '.exe')
try {
    & $compiler /nologo /target:winexe /platform:anycpu /optimize+ /out:$tempExe /win32icon:$stableIcon /reference:System.Windows.Forms.dll $source
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $tempExe -PathType Leaf)) { throw "C# launcher compilation failed with exit $LASTEXITCODE." }
    Assert-GuiExecutable $tempExe
    $large = [IntPtr]::Zero
    $small = [IntPtr]::Zero
    $count = [PackLabLauncherShellProbe]::ExtractIconEx($tempExe, 0, [ref]$large, [ref]$small, 1)
    try {
        if ($count -lt 1 -or ($large -eq [IntPtr]::Zero -and $small -eq [IntPtr]::Zero)) { throw 'Windows Shell could not extract an icon handle from the compiled EXE.' }
    } finally {
        if ($large -ne [IntPtr]::Zero) { [void][PackLabLauncherShellProbe]::DestroyIcon($large) }
        if ($small -ne [IntPtr]::Zero) { [void][PackLabLauncherShellProbe]::DestroyIcon($small) }
    }
    $flags = 0x1 -bor 0x8 # MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH
    if (-not [PackLabLauncherShellProbe]::MoveFileEx($tempExe, $stableExe, $flags)) { throw "Could not atomically publish stable launcher: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())" }
} finally {
    if (Test-Path -LiteralPath $tempExe) { Remove-Item -LiteralPath $tempExe -Force }
}

Assert-GuiExecutable $stableExe
$large = [IntPtr]::Zero
$small = [IntPtr]::Zero
$count = [PackLabLauncherShellProbe]::ExtractIconEx($stableExe, 0, [ref]$large, [ref]$small, 1)
try {
    if ($count -lt 1 -or ($large -eq [IntPtr]::Zero -and $small -eq [IntPtr]::Zero)) { throw 'Stable launcher has no extractable embedded icon.' }
} finally {
    if ($large -ne [IntPtr]::Zero) { [void][PackLabLauncherShellProbe]::DestroyIcon($large) }
    if ($small -ne [IntPtr]::Zero) { [void][PackLabLauncherShellProbe]::DestroyIcon($small) }
}
$hash = Get-Sha256 $stableExe
$bytes = (Get-Item -LiteralPath $stableExe).Length
Write-Output "OWNER_DEV_LAUNCHER_BUILT $compiler $stableExe $hash $bytes GUI_ICON_OK"
