[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string[]]$Path,
    [switch]$AllowMissing,
    [switch]$ScanText
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
$inputs = @()
foreach ($candidate in $Path) {
    $resolved = if ([System.IO.Path]::IsPathRooted($candidate)) {
        $candidate
    } else {
        Join-Path $repositoryRoot $candidate
    }
    if (Test-Path -LiteralPath $resolved) {
        $inputs += [System.IO.Path]::GetFullPath($resolved)
    } elseif (-not $AllowMissing) {
        throw "CI data-safety artifact input is missing."
    }
}

if ($inputs.Count -eq 0) {
    Write-Output "PACKLAB_CI_DATA_GUARD=PASS optional artifact inputs absent"
    exit 0
}

$arguments = @(
    "-m", "tools.ci.ci_data_safety",
    "--repository", $repositoryRoot
)
foreach ($inputPath in $inputs) {
    $arguments += @("--path", $inputPath)
}
if ($ScanText) {
    $arguments += "--scan-text"
}

Push-Location $repositoryRoot
try {
    & python @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "CI data-safety guard rejected an artifact input."
    }
} finally {
    Pop-Location
}
