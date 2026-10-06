[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ownerRoot = Join-Path $env:LOCALAPPDATA 'PackLab\OwnerDev'
$runtimeRoot = Join-Path $ownerRoot 'current'
$manifestPath = Join-Path $runtimeRoot 'owner-dev-runtime.json'
$pythonw = Join-Path $runtimeRoot '.venv\Scripts\pythonw.exe'
$logRoot = Join-Path $ownerRoot 'logs'

try {
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw 'Runtime manifest is missing.' }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ($manifest.smoke_status -ne 'PASS' -or $manifest.source_commit -notmatch '^[0-9a-f]{40}$') {
        throw 'Runtime manifest is invalid or has no successful smoke result.'
    }
    if (-not (Test-Path -LiteralPath $pythonw -PathType Leaf)) { throw 'PackLab Python runtime is missing.' }
    Start-Process -FilePath $pythonw -ArgumentList @('-m', 'packlab_studio') -WorkingDirectory $runtimeRoot
} catch {
    New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
    $logPath = Join-Path $logRoot ('startup-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.log')
    [IO.File]::WriteAllText($logPath, "PackLab Studio could not start.`r`n$($_.Exception.Message)`r`n", [Text.UTF8Encoding]::new($false))
    Add-Type -AssemblyName PresentationFramework
    [void][System.Windows.MessageBox]::Show("PackLab Studio could not start. Details: $logPath", 'PackLab Studio', 'OK', 'Error')
    exit 1
}
