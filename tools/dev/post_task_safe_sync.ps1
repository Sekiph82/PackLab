#requires -Version 5.1
<#
.SYNOPSIS
Safely fast-forward and verify the canonical PackLab owner Desktop checkout.
.DESCRIPTION
Read-only precheck, fetch, then fast-forward only if clean and ancestry-safe.
Never reset, stash, clean, rebase, force-push, delete or overwrite owner work.
The calling Codex task must already be committed/pushed on origin/main.
#>
[CmdletBinding()]
param(
    [string]$Workspace = 'C:\Users\sekip\Desktop\PackLab',
    [switch]$RefreshOwnerDev
)
$ErrorActionPreference = 'Stop'
function Git([string[]]$GitArgs) {
    $result = & git -C $Workspace @GitArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($GitArgs -join ' ') failed: $($result -join '; ')"
    }
    return ($result | Out-String).Trim()
}
try {
    if (-not (Test-Path -LiteralPath $Workspace -PathType Container)) {
        throw "LOCAL_SYNC_PENDING: Workspace does not exist: $Workspace"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $Workspace '.git'))) {
        throw 'LOCAL_SYNC_PENDING: Workspace is not a Git checkout.'
    }
    $root = Git @('rev-parse','--show-toplevel')
    if ([IO.Path]::GetFullPath($root).TrimEnd('\') -ine [IO.Path]::GetFullPath($Workspace).TrimEnd('\')) {
        throw "LOCAL_SYNC_PENDING: Wrong Git root: $root"
    }
    $origin = Git @('remote','get-url','origin')
    if ($origin -notmatch '(?i)(github\.com[:/]Sekiph82/PackLab(\.git)?$)') {
        throw "LOCAL_SYNC_PENDING: Wrong origin: $origin"
    }
    $branch = Git @('branch','--show-current')
    if ($branch -ne 'main') {
        throw "LOCAL_SYNC_PENDING: Owner checkout is not on main ($branch)."
    }
    $dirty = Git @('status','--porcelain=v1','--untracked-files=normal')
    if ($dirty) {
        throw "LOCAL_SYNC_PENDING: Owner checkout has edits/untracked files. Preserve as-is.\n$dirty"
    }
    [void](Git @('fetch','origin','main'))
    $before = Git @('rev-parse','HEAD')
    $remote = Git @('rev-parse','refs/remotes/origin/main')
    $base = Git @('merge-base',$before,$remote)
    if ($base -ne $before) {
        throw "LOCAL_SYNC_PENDING: Local divergence requires owner-safe reconciliation. local=$before remote=$remote"
    }
    if ($before -ne $remote) {
        [void](Git @('merge','--ff-only','refs/remotes/origin/main'))
    }
    $after = Git @('rev-parse','HEAD')
    if ($after -ne $remote) {
        throw "LOCAL_SYNC_PENDING: SHA mismatch after safe fast-forward: local=$after remote=$remote"
    }
    $postDirty = Git @('status','--porcelain=v1','--untracked-files=normal')
    if ($postDirty) {
        throw "LOCAL_SYNC_PENDING: Checkout unexpectedly modified after sync. Preserve and inspect:\n$postDirty"
    }
    Write-Host "DESKTOP_GITHUB_SYNC_PASS local=$after origin/main=$remote"
    if ($RefreshOwnerDev) {
        $refresh = Join-Path $Workspace 'tools\dev\post_codex_owner_dev_refresh.ps1'
        if (-not (Test-Path -LiteralPath $refresh -PathType Leaf)) {
            throw 'OWNERDEV_REFRESH_PENDING: refresh script not found.'
        }
        & $refresh
        if (-not $?) { throw 'OWNERDEV_REFRESH_PENDING: refresh command failed.' }
        Write-Host 'OWNERDEV_REFRESH_INVOKED: verify deployed PackLab.exe SHA/runtime as required by task.'
    }
} catch {
    Write-Error $_
    exit 2
}
