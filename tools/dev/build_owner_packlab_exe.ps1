[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$OwnerRoot = (Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) 'PackLab\OwnerDev'),
    [Parameter(Mandatory=$true)][string]$SourceCommit,
    [Parameter(Mandatory=$true)][string]$RuntimeId
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $RepositoryRoot).Path
$runtime = Join-Path (Join-Path $OwnerRoot 'releases') $RuntimeId
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

function Assert-EmbeddedIcon([string]$Path) {
    $large = [IntPtr]::Zero
    $small = [IntPtr]::Zero
    $count = [PackLabLauncherShellProbe]::ExtractIconEx($Path, 0, [ref]$large, [ref]$small, 1)
    try {
        if ($count -lt 1 -or ($large -eq [IntPtr]::Zero -and $small -eq [IntPtr]::Zero)) { throw "Windows Shell could not extract an icon handle from $Path." }
    } finally {
        if ($large -ne [IntPtr]::Zero) { [void][PackLabLauncherShellProbe]::DestroyIcon($large) }
        if ($small -ne [IntPtr]::Zero) { [void][PackLabLauncherShellProbe]::DestroyIcon($small) }
    }
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

if ($SourceCommit -notmatch '^[0-9a-f]{40}$' -or $RuntimeId -notmatch ('^' + [regex]::Escape($SourceCommit) + '-[0-9a-f]{32}$')) { throw 'Launcher source/runtime identity is invalid.' }
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

$sourceHash = Get-Sha256 $source
$iconHash = Get-Sha256 $stableIcon
$fingerprintPath = Join-Path $launcherDir 'PackLab.build.json'
$reuseExisting = $false
if ((Test-Path -LiteralPath $stableExe -PathType Leaf) -and (Test-Path -LiteralPath $fingerprintPath -PathType Leaf)) {
    try {
        $fingerprint = Get-Content -LiteralPath $fingerprintPath -Raw | ConvertFrom-Json
        $reuseExisting = ($fingerprint.source_sha256 -eq $sourceHash -and $fingerprint.source_commit -eq $SourceCommit -and $fingerprint.runtime_id -eq $RuntimeId -and $fingerprint.owner_root -eq $OwnerRoot -and $fingerprint.icon_sha256 -eq $iconHash -and $fingerprint.compiler_path -eq $compiler)
        if ($reuseExisting) { Assert-GuiExecutable $stableExe; Assert-EmbeddedIcon $stableExe }
    } catch { $reuseExisting = $false }
}

if (-not $reuseExisting) {
    $tempExe = Join-Path $launcherDir ('PackLab-' + [guid]::NewGuid().ToString('N') + '.exe')
    $tempSource = Join-Path $launcherDir ('PackLab-' + [guid]::NewGuid().ToString('N') + '.cs')
    try {
        $launcherSource = [IO.File]::ReadAllText($source)
        $ownerRootLiteral = $OwnerRoot.Replace('\', '\\').Replace('"', '\"')
        $launcherSource = $launcherSource.Replace('__PACKLAB_SOURCE_COMMIT__', $SourceCommit).Replace('__PACKLAB_RUNTIME_ID__', $RuntimeId).Replace('__PACKLAB_OWNER_ROOT__', $ownerRootLiteral)
        [IO.File]::WriteAllText($tempSource, $launcherSource, [Text.UTF8Encoding]::new($false))
        & $compiler /nologo /target:winexe /platform:anycpu /optimize+ /out:$tempExe /win32icon:$stableIcon /reference:System.Windows.Forms.dll $tempSource
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $tempExe -PathType Leaf)) { throw "C# launcher compilation failed with exit $LASTEXITCODE." }
        Assert-GuiExecutable $tempExe
        Assert-EmbeddedIcon $tempExe
        $flags = 0x1 -bor 0x8 # MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH
        if (-not [PackLabLauncherShellProbe]::MoveFileEx($tempExe, $stableExe, $flags)) { throw "Could not atomically publish stable launcher: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())" }
    } finally {
        if (Test-Path -LiteralPath $tempExe) { Remove-Item -LiteralPath $tempExe -Force }
        if (Test-Path -LiteralPath $tempSource) { Remove-Item -LiteralPath $tempSource -Force }
    }
}

Assert-GuiExecutable $stableExe
Assert-EmbeddedIcon $stableExe
$hash = Get-Sha256 $stableExe
$bytes = (Get-Item -LiteralPath $stableExe).Length
$fingerprint = [ordered]@{ source_sha256 = $sourceHash; source_commit = $SourceCommit; runtime_id = $RuntimeId; owner_root = $OwnerRoot; icon_sha256 = $iconHash; compiler_path = $compiler; exe_sha256 = $hash; exe_bytes = $bytes } | ConvertTo-Json
$fingerprintTemp = Join-Path $launcherDir ('PackLab.build-' + [guid]::NewGuid().ToString('N') + '.json')
[IO.File]::WriteAllText($fingerprintTemp, $fingerprint + "`n", [Text.UTF8Encoding]::new($false))
if (-not [PackLabLauncherShellProbe]::MoveFileEx($fingerprintTemp, $fingerprintPath, (0x1 -bor 0x8))) {
    Remove-Item -LiteralPath $fingerprintTemp -Force -ErrorAction SilentlyContinue
    throw "Could not atomically publish launcher fingerprint: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
}
$result = if ($reuseExisting) { 'OWNER_DEV_LAUNCHER_REUSED' } else { 'OWNER_DEV_LAUNCHER_BUILT' }
Write-Output "$result $SourceCommit $RuntimeId $compiler $stableExe $hash $bytes GUI_ICON_OK"
