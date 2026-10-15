# PackLab M16 | Release Control: Offline Preparation (2026-10-15)

**Scope:** Source-grounded preliminary design for PL-0363 (version train), PL-0364 (release manifest), PL-0365 (changelog), PL-0366 (release gates), and PL-0367 (rollback). These are **DRAFT CONTRACTS ONLY**, not acceptance of a PL task or authorization to create a release. Created with ZERO GitHub Actions runs.

## 1. Three-version model, no forced numeric alignment

| Domain | Authoritative source inspected | Observed development value | Meaning |
| --- | --- | --- | --- |
| `StudioVersion` | PL0350 Installer/report and release-policy references | `0.1.0` in last accepted engineering packaging | Windows Studio application; re-read actual source before locking a future release |
| `CaptureVersion` | `apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj` and `Info.plist` | `0.1.0`; numeric app build `1` | iOS app version/build; **not** a signed/shipped binary |
| `PackScanSchemaVersion` | `schemas/packscan/manifest.schema.json` | `1.0.0` | Canonical `.packscan` capture-container contract |

Per `docs/architecture/VERSIONING_POLICY.md`, these domain versions advance independently. A release-train identifier may group artifacts and exact build/source SHA without pretending versions are equal or that a draft train has shipped.

**Future manifest contract, not a generated release artifact:**

```yaml
manifest_status: DRAFT_UNVALIDATED
release_train_id: null  # mandatory only for a real release candidate
studio: { version: null, source_sha: null, artifact_sha256: null, signing: UNKNOWN }
capture: { version: null, build: null, source_sha: null, artifact_sha256: null, signing: UNKNOWN }
packscan: { schema_written: "1.0.0", schema_read_min: null, schema_read_max: null }
windows: { python: null, qt: null, occt: null, ocp: null, open3d: null, notices_ref: null }
ios: { xcode: null, swift: null, nextlevel_pin: "0.19.1", provisioning: UNKNOWN }
rights: { formal_legal_review: PENDING, factory_distribution: NOT_AUTHORIZED }
acceptance: { pl0354_full_xctest: BLOCKED, m17: NOT_ACCEPTED, pl0368_release: DEFERRED }
```

**Null is deliberately a failure/incompleteness marker.** A future validated generator must populate exact source/build-provenance facts and fail closed on missing required artifact hashes, source and notices, supported schema range, signing state or independent audit. Do not treat the example as a real release manifest.

## 2. Changelog policy prepared for PL-0365

Use explicit, reviewed task IDs (e.g., `PL-0350`) and separately approved human summaries. Cross-check each against root `TASKS.md` and independent ChatGPT audit, never Codex `READY` alone. Reject duplicate/unknown/unaccepted IDs, incompatible release scope, unverifiable milestone acceptance and notes that expose private data. Sort by milestone/task ID into `Added`, `Changed`, `Fixed`, `Security`, `Known limitations`. Cite exact SHA and affected version domain; no arbitrary commit-message scraping. No public `CHANGELOG` publication or release tag before PL-0368 owner/M17 gate.

## 3. PL-0366 release checklist, explicit current BLOCKED status

| Required gate | Observed evidence | Current decision |
| --- | --- | --- |
| Windows Installer build + installed offline smoke | PL0350/PL0351 audits PASS; exact accepted warm Installer published privately | ENGINEERING PASS only |
| Private Installer retention | PL0352 artifact `11959245441` until 2026-12-14, readback PASS | TIME-LIMITED, NOT permanent |
| CI protected from private sample datasets | PL0353 V02 audit PASS, five fail-closed upload guards | ENGINEERING PASS |
| iOS Capture simulator all XCTest | Targeted run `38767357450` 25/25 PASS; **full final 205 not run**, `38770566255` billing-blocked; older run 173/205 | **BLOCKED** |
| iOS unsigned device archive / physical install | Not accepted; no validated signed IPA | NOT ACCEPTED |
| Signing credentials / secrets review | No signed workflow authorized; no Apple credentials may be stored in repo | SEPARATE REVIEW REQUIRED |
| Windows redistribution compliance | PL0350 automated engineering inventory mapped all staged files; formal legal review unresolved | **FORMAL LEGAL PENDING** |
| Version compatibility / release manifest / changelog | This draft only; authoritative generator not yet audited | NOT IMPLEMENTED |
| PackScan migration / physical benchmark | M09 owner physical validation deferred; M17 acceptance not completed | **BLOCKED** |
| Internal release `PL-0368` | Explicitly `DEFERRED_POST_M17` | **FORBIDDEN** |

**A future gate validator must reject any release when a mandatory row is missing or not independently accepted.** Private repository status is not legal distribution permission. A validated local Windows Installer is not proof of an approved signed iPhone application. Do not combine them into a misleading "ready for factory" claim.

## 4. No-Actions engineering preparation that remains valid

- Static contracts for missing manifest fields, accepted audit ID mapping and sample-safe changelog fragments can be designed/reviewed offline.
- Source-only comparison of schema and API capabilities can be performed without native compilation, making a **draft** compatibility matrix. Do not assert actual read/write support from version proximity.
- Risk/compliance analysis, documented iPhone install/reinstall steps, safe rollback and non-destructive data backup can be finalized as policy drafts pending executed device acceptance.
- Existing workflow YAML and CI selectors may be **read-only audited** without runner dispatch. Do not push changes to `.github/workflows/**`, `apps/ios-capture/**`, `tools/**`, `tests/**` or other path-triggered areas onto `main` during the zero-Actions work mode.

## 5. No-action budget and authorization

Owner reported **USD 56.92** Actions spending in approximately one week. No GitHub Actions, retry, paid alternative CI, invoice/payment change, new build artifact or signing request is authorized through October. Docs/coordination-only commits do not match the *currently inspected* automatic workflow push path filters; inspect any new filters before further pushes. GitHub existing storage may still incur fees and must not be misrepresented as guaranteed free. Resume **only** on a new explicit owner instruction; November is not automatic permission.

**References:** `docs/development/NO_ACTIONS_OFFLINE_WORK_POLICY_2026-10-15.md`, `docs/architecture/VERSIONING_POLICY.md`, `docs/packscan/container-layout.md`, `docs/packaging/PL0362_PL0367_OFFLINE_INSTALL_ROLLBACK_PREPARATION.md`, `docs/packaging/GITHUB_ACTIONS_ARTIFACT_RETENTION_POLICY.md`, and `coordination/sessions/M16-C001/PL-0354_CHATGPT_AUDIT_V02.md`.
