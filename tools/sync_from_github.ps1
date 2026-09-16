param(
    [string]$TargetPath = "C:\Users\sekip\Desktop\PackLab",
    [string]$RepositoryUrl = "https://github.com/Sekiph82/PackLab.git",
    [string]$Branch = "main",
    [switch]$IncludeIgnored
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [string]$WorkingDirectory = $TargetPath
    )

    Push-Location $WorkingDirectory
    try {
        & git @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "git $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}

function Get-GitText {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [string]$WorkingDirectory = $TargetPath
    )

    Push-Location $WorkingDirectory
    try {
        $output = & git @Arguments 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "git $($Arguments -join ' ') failed: $output"
        }
        return ($output | Out-String).Trim()
    }
    finally {
        Pop-Location
    }
}

function Normalize-RemoteUrl {
    param([string]$Url)

    $normalized = $Url.Trim().TrimEnd('/')
    if ($normalized.EndsWith('.git')) {
        $normalized = $normalized.Substring(0, $normalized.Length - 4)
    }
    return $normalized.ToLowerInvariant()
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is not installed or is not available on PATH."
}

Write-Host "PackLab authoritative sync"
Write-Host "GitHub source : $RepositoryUrl ($Branch)"
Write-Host "Local target  : $TargetPath"
Write-Host "Policy        : GitHub wins; local tracked/untracked changes may be deleted."

if (-not (Test-Path $TargetPath)) {
    $parent = Split-Path -Parent $TargetPath
    if ($parent -and -not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }

    & git clone --branch $Branch --single-branch $RepositoryUrl $TargetPath
    if ($LASTEXITCODE -ne 0) {
        throw "Initial clone failed with exit code $LASTEXITCODE"
    }
}
elseif (-not (Test-Path (Join-Path $TargetPath '.git'))) {
    throw "Target exists but is not a Git repository: $TargetPath. Refusing to delete arbitrary local files."
}

$origin = Get-GitText -Arguments @('remote', 'get-url', 'origin')
$expected = Normalize-RemoteUrl $RepositoryUrl
$actual = Normalize-RemoteUrl $origin

$sshExpected = 'git@github.com:sekiph82/packlab'
if (($actual -ne $expected) -and ($actual -ne $sshExpected)) {
    throw "Origin mismatch. Expected Sekiph82/PackLab, found: $origin"
}

Write-Host "Fetching authoritative GitHub state..."
Invoke-Git -Arguments @('fetch', 'origin', $Branch, '--prune')

Write-Host "Discarding local tracked changes and switching to origin/$Branch..."
Invoke-Git -Arguments @('checkout', '-B', $Branch, "origin/$Branch", '--force')
Invoke-Git -Arguments @('reset', '--hard', "origin/$Branch")

if ($IncludeIgnored) {
    Write-Host "Removing untracked AND ignored files..."
    Invoke-Git -Arguments @('clean', '-fdx')
}
else {
    Write-Host "Removing untracked files/directories; ignored runtime/cache files are preserved..."
    Invoke-Git -Arguments @('clean', '-fd')
}

$localHead = Get-GitText -Arguments @('rev-parse', 'HEAD')
$remoteHead = Get-GitText -Arguments @('rev-parse', "origin/$Branch")
$status = Get-GitText -Arguments @('status', '--porcelain')

if ($localHead -ne $remoteHead) {
    throw "Synchronization verification failed: local HEAD does not equal origin/$Branch."
}

if ($status) {
    throw "Synchronization verification failed: working tree is not clean:`n$status"
}

Write-Host ""
Write-Host "SUCCESS: $TargetPath now matches GitHub origin/$Branch for all tracked and non-ignored files."
Write-Host "HEAD: $localHead"
if (-not $IncludeIgnored) {
    Write-Host "Ignored files (for example caches/virtual environments) were intentionally preserved."
}
