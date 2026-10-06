[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ownerRoot = Join-Path $env:LOCALAPPDATA 'PackLab\OwnerDev'
$runtimeRoot = Join-Path $ownerRoot 'current'
$manifestPath = Join-Path $runtimeRoot 'owner-dev-runtime.json'
$pythonw = Join-Path $runtimeRoot '.venv\Scripts\pythonw.exe'
$studioSource = Join-Path $runtimeRoot 'apps\windows-studio\src'
$coreSource = Join-Path $runtimeRoot 'core\src'
$logRoot = Join-Path $ownerRoot 'logs'

try {
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw 'Runtime manifest is missing.' }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ($manifest.smoke_status -ne 'PASS' -or $manifest.source_commit -notmatch '^[0-9a-f]{40}$') {
        throw 'Runtime manifest is invalid or has no successful smoke result.'
    }
    if (-not (Test-Path -LiteralPath $pythonw -PathType Leaf)) { throw 'PackLab Python runtime is missing.' }
    if (-not (Test-Path -LiteralPath $studioSource -PathType Container) -or -not (Test-Path -LiteralPath $coreSource -PathType Container)) { throw 'PackLab source modules are missing.' }
    $bootstrap = "import os,sys,runpy;sys.path[:0]=[os.path.join(os.environ['LOCALAPPDATA'],'PackLab','OwnerDev','current','core','src'),os.path.join(os.environ['LOCALAPPDATA'],'PackLab','OwnerDev','current','apps','windows-studio','src')];runpy.run_module('packlab_studio',run_name='__main__')"
    Start-Process -FilePath $pythonw -ArgumentList @('-c', $bootstrap) -WorkingDirectory $runtimeRoot
} catch {
    New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
    $logPath = Join-Path $logRoot ('startup-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.log')
    [IO.File]::WriteAllText($logPath, "PackLab Studio could not start.`r`n$($_.Exception.Message)`r`n", [Text.UTF8Encoding]::new($false))
    Add-Type -AssemblyName PresentationFramework
    [void][System.Windows.MessageBox]::Show("PackLab Studio could not start. Details: $logPath", 'PackLab Studio', 'OK', 'Error')
    exit 1
}
