# PL-0353 | ChatGPT Independent Audit V01 — 2026-10-15

**VERDICT: AUDITED_PARTIAL_CHANGES_REQUIRED / ONE CONFIRMED FAIL-CLOSED UPLOAD BYPASS.**
Quality and preview work **pass** but the task is **NOT CLOSED** because several GitHub Actions artifact uploads use unconditional `if: always()` even if their preceding new sensitive-data guards fail. This violates PL0353's purpose and criterion 4/5. Fix only this narrow gate, verify without native rebuild, then re-audit. **No actual proprietary-data leak is known or claimed.**

## Evidence independently read

- Live private repository metadata `private=true`, default `main`, at initial audit `main=6b7f32d293dbc217b1aa9f622e3836f431c97503`. Latest commit `6b7f32d2` changed only `coordination/sessions/M16-C001/PL-0353_CODEX_LOG_V02.md`, separately from implementation.
- Builder report: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0353_CODEX_LOG_V02.md
- Windows Quality run https://github.com/Sekiph82/PackLab/actions/runs/38713322342, job **116349860746** independent log read: `PACKLAB_CI_DATA_GUARD=PASS`, Ruff PASS, mypy `Success: no issues found in 254 source files`, **2,218 passed, 10 skipped, 1 deselected, 2 warnings** (201.96 seconds), job success, head `68a560e446070b938c31eb2595056448123d612f`. This was a real hosted fresh checkout.
- Windows Studio Preview run https://github.com/Sekiph82/PackLab/actions/runs/38712670742, job **116347663871** independent log read: source guard PASS, post-build EXE + setup artifact guard PASS, artifact ID **11960773724** 23,672,631 bytes SHA256 `552d03b2e96f48fb06d5f3a37902c44acbd414e97fb6c993020d7e1f125bb5d0`, 1-day retention, job success, tested implementation prior to small PL0352 expiry type repair.
- Retained exact PL0352 private Installer independently still present in producer artifact metadata **11959245441**, bytes **877,601,969**, SHA256 `b976c7d4e48985329c8f51a68b250ff6e565930ed993b0409b9c5d561c3da4ac`, expires 2026-12-14 08:38:33 UTC. No new native OCP/OCCT or Installer build in inspected PL0353 Actions runs.
- Source independently read: `tools/ci/ci_data_safety.py`, `tools/ci/ci_safe_data_policy.json`, `tools/ci/scan_artifact_inputs.ps1`, data-safety tests, actual Windows quality/preview/full Studio/fmt-probe/SDK-recovery GitHub workflow conditions. **68 focused tests PASS per builder log** (not independently rerun).
- Valid positives: six small deterministic fixtures PNG/JPG/STL/PLY/STEP/DXF and three preexisting hash/size-approved assets. New scanner checks private path families, byte-change in allowlisted payloads, raw scan formats, text diagnostics for owner paths, size-bound raw inputs, and basic link/ZIP-member safety, and avoids logging paths/content. Synthetic negative test cases are present. Source-local helper `tools/sync_from_github.ps1` not linked from CI, according to builder audit.

## Confirmed blocking finding: always() bypasses failure of new guards

On actual GitHub main workflows, the upload actions **remain eligible after their preceding guard fails**, because both the guard and upload have `if: always()`. GitHub evaluates that condition independently of an earlier step's failure. The upload can therefore collect the very artifact that was rejected.

Four confirmed vulnerable pairs:

1. `.github/workflows/windows-studio-build.yml`, step **Guard precompile diagnostic artifact inputs** `if: always()`, immediately followed by **Upload noncompiling SDK and native runtime diagnostic evidence** `if: always()`. Guard runs but does not gate upload.
2. Same file, **Guard OCP quarantine artifact inputs** `if: always()`, followed by **Upload post-link OCP quarantine before any downstream failure can discard it** `if: always()`.
3. Same file, **Guard packaged Studio smoke diagnostic inputs** `if: always()`, followed by **Upload packaged Studio smoke diagnostics** `if: always()`.
4. `.github/workflows/pl0350-fmt-dependency-probe.yml`, **Guard dependency probe artifact input** `if: always()`, followed by **Upload dependency probe evidence** `if: always()`.

In each pair, a guard rejection marks the step failed, but the subsequent unconditional `always()` still executes the upload. A private repository is not an excuse for leaking protected owner/supplier material to accessible Actions artifacts. **This is an independently confirmed source-level failure**, not an assumption based on missing CI runs. No actual such leak was observed in completed Quality/Preview runs, which pass.

Check all other actual upload `if: always()` or equivalent status-function chains for the same issue. Do not make these 6h native workflows auto-run merely to validate this fix.

### Required narrow repair (same PL-0353)

- Assign a unique, reliable step `id:` to each guard and make every associated upload explicitly depend on that guard's `outcome == 'success'`, while preserving ability to upload **approved diagnostics** after earlier unrelated stage errors: `if: always() && steps.<guard_id>.outcome == 'success'`. Keep the guard `if: always()` where intended. If the guard fails or is skipped, upload MUST skip/fail closed.
- Ensure scanner rejects bad payloads in real upload boundaries, and do not let an `if: always()` cleanup path bypass guard failure.
- Add targeted YAML/workflow contract negative tests asserting ALL four chains, including guard failure, missing inputs, correct behavior on unrelated earlier job failure with guard success. Test other relevant `always()` conditions too.
- Run focused pytest/YAML/Ruff/format/mypy where changed, optionally a small hosted workflow parsing check, **without OCCT/OCP/native compilation or Installer rebuild**. Previous real hosted Quality/Preview PASS remains accepted for the unchanged core. Publish implementation then separate updated Codex log. Stay PL0353; Codex MUST NOT edit root TASKS.md.

## Acceptance status

- **ACCEPTED**: clean hosted default Quality 2,218 pass, 10 skip, 1 deselect; Preview standalone EXE/setup and its guard; synthetic fixture policy/scanner tests; private repo; existing accepted installer preserved; no unauthorized product/release changes observed.
- **BLOCKED**: `if: always()` uploader bypass. The new sensitive-data guard does not actually prevent upload on at least four paths. PL0353 cannot be marked PASS or advance to PL0354 until fixed and audited.
- **NOT TESTED**: full OCCT/OCP Windows packaging with new guards. It must not be described as currently passed; no costly recompilation is required for narrow workflow conditional repair. Retained PL0352 installer remains historically valid.
- **LIMITATIONS**: GitHub evidence cannot independently confirm owner's laptop untouched; builder reports so. Live actor-relative private data safety is bounded to implemented scanner and test scope, not a forensic guarantee over all future content. Legal review and Kenya factory rollout remain not authorized.

**Next Codex instruction:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0353_R01_FAIL_CLOSED_UPLOAD_GATE_CODEX_PROMPT.md

**Formal flags:** `legal_review_required=true`, `public_release_authorized=false`.
