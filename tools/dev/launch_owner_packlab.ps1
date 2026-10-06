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
$startupLog = Join-Path $logRoot ('startup-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.log')

try {
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw 'Runtime manifest is missing.' }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ($manifest.smoke_status -ne 'PASS' -or $manifest.source_commit -notmatch '^[0-9a-f]{40}$') {
        throw 'Runtime manifest is invalid or has no successful smoke result.'
    }
    if ($manifest.studio_version -notmatch '^\d+\.\d+\.\d+') { throw 'Runtime manifest has an invalid Studio version.' }
    if (-not (Test-Path -LiteralPath $pythonw -PathType Leaf)) { throw 'PackLab Python runtime is missing.' }
    if (-not (Test-Path -LiteralPath $studioSource -PathType Container) -or -not (Test-Path -LiteralPath $coreSource -PathType Container)) { throw 'PackLab source modules are missing.' }
    $bootstrap = "import os,sys,runpy;sys.path[:0]=[os.path.join(os.environ['LOCALAPPDATA'],'PackLab','OwnerDev','current','core','src'),os.path.join(os.environ['LOCALAPPDATA'],'PackLab','OwnerDev','current','apps','windows-studio','src')];runpy.run_module('packlab_studio',run_name='__main__')"
    New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
    $previousDiagnosticMode = $env:PACKLAB_OWNERDEV_DIAGNOSTICS
    $previousStartupLog = $env:PACKLAB_OWNERDEV_STARTUP_LOG
    $previousSourceSha = $env:PACKLAB_OWNERDEV_SOURCE_SHA
    $previousStudioVersion = $env:PACKLAB_OWNERDEV_STUDIO_VERSION
    try {
        $env:PACKLAB_OWNERDEV_DIAGNOSTICS = '1'
        $env:PACKLAB_OWNERDEV_STARTUP_LOG = $startupLog
        $env:PACKLAB_OWNERDEV_SOURCE_SHA = [string]$manifest.source_commit
        $env:PACKLAB_OWNERDEV_STUDIO_VERSION = [string]$manifest.studio_version
        $child = Start-Process -FilePath $pythonw -ArgumentList @('-c', "`"$bootstrap`"") -WorkingDirectory $runtimeRoot -PassThru
    } finally {
        $env:PACKLAB_OWNERDEV_DIAGNOSTICS = $previousDiagnosticMode
        $env:PACKLAB_OWNERDEV_STARTUP_LOG = $previousStartupLog
        $env:PACKLAB_OWNERDEV_SOURCE_SHA = $previousSourceSha
        $env:PACKLAB_OWNERDEV_STUDIO_VERSION = $previousStudioVersion
    }
    $stabilityDeadline = [DateTime]::UtcNow.AddSeconds(8)
    while ([DateTime]::UtcNow -lt $stabilityDeadline) {
        $child.Refresh()
        if ($child.HasExited) {
            $exitCode = $child.ExitCode
            $diagnostic = @(
                'PackLab OWNER DEV child exited during the startup stability window.'
                "timestamp_utc=$([DateTime]::UtcNow.ToString('o'))"
                "reason=early_child_exit"
                "exit_code=$exitCode"
                "deployed_sha=$($manifest.source_commit)"
                "studio_version=$($manifest.studio_version)"
                "python_version=$($manifest.python_version)"
                "startup_exception_log=$startupLog"
            ) -join "`r`n"
            if (Test-Path -LiteralPath $startupLog -PathType Leaf) {
                $diagnostic += "`r`n`r`nstartup_exception_details:`r`n" + (Get-Content -LiteralPath $startupLog -Raw)
            }
            [IO.File]::WriteAllText($startupLog, $diagnostic + "`r`n", [Text.UTF8Encoding]::new($false))
            Add-Type -AssemblyName PresentationFramework
            [void][System.Windows.MessageBox]::Show("PackLab Studio exited during startup (code $exitCode). Details: $startupLog", 'PackLab Studio', 'OK', 'Error')
            exit 1
        }
        Start-Sleep -Milliseconds 250
    }
} catch {
    New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
    $logPath = Join-Path $logRoot ('startup-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.log')
    [IO.File]::WriteAllText($logPath, "PackLab Studio could not start.`r`nreason=launcher_failure`r`ndeployed_sha=$($manifest.source_commit)`r`nstudio_version=$($manifest.studio_version)`r`n$($_.Exception.Message)`r`n", [Text.UTF8Encoding]::new($false))
    Add-Type -AssemblyName PresentationFramework
    [void][System.Windows.MessageBox]::Show("PackLab Studio could not start. Details: $logPath", 'PackLab Studio', 'OK', 'Error')
    exit 1
}
