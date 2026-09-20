$ErrorActionPreference = "Stop"

$requiredPython = "3.12.10"
$requiredUv = "0.11.26"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $repoRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python $requiredPython is required but was not found on PATH."
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv $requiredUv is required but was not found on PATH. Install it using the public upstream instructions, then rerun."
}

$pythonVersion = (& python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))").Trim()
if ($pythonVersion -ne $requiredPython) {
    throw "Expected CPython $requiredPython; found $pythonVersion."
}
$uvVersion = (& uv --version).Trim() -replace '^uv\s+', '' -replace '\s+.*$', ''
if ($uvVersion -ne $requiredUv) {
    throw "Expected uv $requiredUv; found $uvVersion."
}
foreach ($requiredFile in @("pyproject.toml", "uv.lock", ".python-version")) {
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $requiredFile) -PathType Leaf)) {
        throw "Required repository file is missing: $requiredFile"
    }
}

Write-Host "Synchronizing the locked M01 development environment with uv $requiredUv..."
& uv sync --locked --dev
if ($LASTEXITCODE -ne 0) {
    throw "uv sync --locked --dev failed with exit code $LASTEXITCODE."
}
Write-Host "PackLab Windows bootstrap completed idempotently."
