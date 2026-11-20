# CLAUDE_PEER_REVIEW — PR #6 signed IPA iOS 18.0 platform guard (V01)

Reviewer: Claude independent source reviewer (subagent), not the builder. Read-only except this file.
Scope: `git diff main...fix/signed-ipa-ios-platform` (head 0d05f6db): `.github/workflows/packlab-capture-signed-ipa.yml` (+19/-1), `tests/ci/test_capture_signed_ipa_workflow.py` (+10).

## Verdict: PASS_WITH_NOTES

## Evidence I gathered myself
- `python -m pytest tests/ci/test_capture_signed_ipa_workflow.py -q` -> 16 passed (local, Windows, Git Bash available).
- Ran the new regexes through `grep -ciE` on a fixture log: compile regex matched the `X.swift:12:5: error: cannot find ...` line only (1), not a `warning:` line with "expected "; platform regex matched both `error: iOS 18.0 is not installed...` and `xcodebuild: error: Unable to find a destination...` (2); total `error:` unchanged (4). Both are valid ERE.
- Compared against the accepted Simulator step in `.github/workflows/packlab-capture-macos.yml:342-354`. The new step uses the same check, download and import commands (minus `-showdestinations`, which only matters for the Simulator).

## Checks
1. Step correctness/order (workflow lines 107-123): it runs after "Select Xcode and record signing toolchain" (xcode-select to Xcode_16.app at line 87) and before NextLevel resolve, keychain install and archive. It has the same `configured == 'true'` guard as its sibling steps. `set -euo pipefail` plus a final `has_runtime` makes the step fail if the runtime is still missing after import. `-downloadPlatform iOS` without `-buildVersion` gets the platform that matches the selected Xcode 16.0, which is iOS 18.0. `-exportPath` and `-importPlatform <dmg>` are used correctly. The simctl iOS-18-0 runtime check is a proxy, but it is the right one: since Xcode 15 the iOS platform support needed by a `generic/platform=iOS` archive ships as the downloadable iOS component installed by `-downloadPlatform iOS`, and the known runner-image failure ("iOS N is not installed") is fixed by exactly this download.
2. Leak safety (line 335): `report_failure` still only echoes `grep -c` counts and fixed labels. The existing static test (no `$log`/`$2` in echo lines, no cat/tail/head/sed/awk) still covers it. The new step runs before any signing material is decoded and no secrets are in job env, so `downloadPlatform` progress output in the public log has nothing sensitive to leak.
3. Tests: the new `test_ios_platform_is_ensured_before_archive` checks order, the download/import commands and the final post-check. It is structural, which is appropriate for a workflow file.
4. Cost: the download is several GB and takes minutes, but only when the runtime is missing. The job stays dispatch-only on `main` with a 45-minute timeout. No new triggers, permissions, artifacts or secrets.

## Notes (non-blocking)
- N1 (Low, tests): no test exercises the new `platform=` category or the narrowed `compile=` regex. `test_failure_report_emits_only_a_count` (test file line 292) still passes only because it does a substring match on the old prefix. Suggestion: add a fixture line `error: iOS 18.0 is not installed.` and assert `compile=0 platform=1`.
- N2 (Info): the root-cause hypothesis is not proven. Run 44731722064's log is runner-only and the counts showed no platform category at the time. The first signed run after merge will confirm it: look for `platform=` > 0 on failure, or the summary line "downloaded (absent on runner image)". If it fails again with `platform=0`, look elsewhere (e.g. scheme/destination resolution).
- N3 (Info): `destination` in the platform regex is broad. That is harmless because only counts are printed.
- N4 (Info): `has_runtime` duplicates the Simulator job's jq expression. That is acceptable; do not extract it.

No CHANGES_REQUIRED findings.
