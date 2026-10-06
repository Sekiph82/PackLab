[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [switch]$AllowPublishedCommit,
    [string]$UvPath
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $RepositoryRoot).Path
$gitRoot = (& git -C $root rev-parse --show-toplevel).Trim()
if ((Resolve-Path -LiteralPath $gitRoot).Path -ne $root) { throw 'RepositoryRoot is not the Git worktree root.' }
$sha = (& git -C $root rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $sha -notmatch '^[0-9a-f]{40}$') { throw 'Could not resolve exact HEAD.' }
$status = @(& git -C $root status --porcelain=v1)
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect Git status.' }
if ($status.Count -gt 0) { throw 'Runtime refresh requires a clean Git worktree.' }
if ($AllowPublishedCommit) {
    $published = (& git -C $root rev-parse origin/main).Trim()
    if ($LASTEXITCODE -ne 0 -or $published -ne $sha) { throw 'HEAD does not exactly match origin/main.' }
}

$ownerRoot = Join-Path $env:LOCALAPPDATA 'PackLab\OwnerDev'
New-Item -ItemType Directory -Force -Path $ownerRoot | Out-Null
$stage = Join-Path $ownerRoot ('stage-' + [guid]::NewGuid().ToString('N'))
$current = Join-Path $ownerRoot 'current'
$backup = Join-Path $ownerRoot ('previous-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $stage | Out-Null

function Get-Sha256([string]$Path) {
    $algorithm = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try { return [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose(); $algorithm.Dispose() }
}

try {
    $include = @('pyproject.toml', 'uv.lock', 'core/src', 'apps/windows-studio/src', 'apps/windows-studio/assets/branding', 'schemas', 'assets', 'tools/dev/launch_owner_packlab.ps1')
    $trackedPaths = @(& git -C $root ls-tree -r --name-only $sha -- $include)
    if ($LASTEXITCODE -ne 0 -or $trackedPaths.Count -eq 0) { throw 'Could not enumerate tracked runtime files from HEAD.' }
    foreach ($relativePath in $trackedPaths) {
        if ($relativePath -match '(^|/)(\.git|__pycache__|\.pytest_cache|build|dist|tests|coordination)(/|$)|(^|/)\.env(?:\.|$)|\.(?:pem|p12|key)$') {
            throw "Refusing an excluded path in the runtime allowlist: $relativePath"
        }
        $source = Join-Path $root $relativePath
        $sourceItem = Get-Item -LiteralPath $source -Force -ErrorAction Stop
        if (($sourceItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Refusing a reparse point in runtime source: $relativePath" }
        $destination = Join-Path $stage $relativePath
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
        Copy-Item -LiteralPath $source -Destination $destination -Force
    }
    $uv = if ($UvPath) { (Resolve-Path -LiteralPath $UvPath).Path } else { (Get-Command uv -ErrorAction Stop).Source }
    & $uv sync --locked --no-install-project --project $stage
    if ($LASTEXITCODE -ne 0) { throw "uv sync --locked failed with exit $LASTEXITCODE." }
    $python = Join-Path $stage '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) { throw 'uv sync did not create the runtime Python executable.' }
    $sourcePaths = ConvertTo-Json -InputObject @((Join-Path $stage 'core\src'), (Join-Path $stage 'apps\windows-studio\src')) -Compress
    $smoke = "import sys; sys.path[:0]=$sourcePaths; from PySide6.QtCore import QTimer; from packlab_studio.app import create_application; from packlab_studio.shell import StudioMainWindow; app=create_application(['PackLab owner runtime smoke']); window=StudioMainWindow(); window.show(); app.processEvents(); assert not window.windowIcon().isNull(), 'canonical icon did not load'; QTimer.singleShot(250, app.quit); raise SystemExit(app.exec())"
    & $python -c $smoke
    $smokeExit = $LASTEXITCODE
    if ($smokeExit -ne 0) { throw "Source-mode Studio smoke failed with exit $smokeExit." }
    $icon = Join-Path $stage 'apps\windows-studio\assets\branding\PackLab.ico'
    $iconHash = Get-Sha256 $icon
    $versionCode = "import sys; sys.path[:0]=$sourcePaths; from packlab_studio import __version__; print(__version__)"
    $version = (& $python -c $versionCode).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Could not read Studio version.' }
    $pythonVersion = (& $python --version 2>&1 | Out-String).Trim()
    $manifest = [ordered]@{
        schema_version = 1
        source_commit = $sha
        studio_version = $version
        python_version = $pythonVersion
        icon_sha256 = $iconHash
        refreshed_utc = [DateTime]::UtcNow.ToString('o')
        smoke_status = 'PASS'
    } | ConvertTo-Json
    [IO.File]::WriteAllText((Join-Path $stage 'owner-dev-runtime.json'), $manifest + "`n", [Text.UTF8Encoding]::new($false))

    if (Test-Path -LiteralPath $current) { Move-Item -LiteralPath $current -Destination $backup }
    try {
        Move-Item -LiteralPath $stage -Destination $current
    } catch {
        if (Test-Path -LiteralPath $backup) { Move-Item -LiteralPath $backup -Destination $current }
        throw
    }
    Write-Output "OWNER_DEV_RUNTIME_UPDATED $sha $current"
} catch {
    if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
    throw
}
