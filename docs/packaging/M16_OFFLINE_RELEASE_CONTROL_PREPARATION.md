# PackLab M16 | Release Control: Offline Preparation (2026-10-15; status refreshed 2026-11-04)

> **2026-11-04 CURRENT MODE:** The owner authorized Codex to select all dependency-safe PL tasks, use GitHub Actions, assign separate peer reviews and update the sole `TASKS.md` tracker after genuine task acceptance. Any older ChatGPT-only, stop-after-child or zero-Actions instructions below are historical, superseded as workflow restrictions by `AGENTS.md` and `coordination/AUTONOMOUS_EXECUTION_POLICY.md`; engineering, secrets, licensing, physical and release evidence obligations remain.


**Scope:** Source-grounded preliminary design for PL-0363 (version train), PL-0364 (release manifest), PL-0365 (changelog), PL-0366 (release gates), and PL-0367 (rollback). These are **DRAFT CONTRACTS ONLY**, not acceptance of a PL task or authorization to create a release. Created with ZERO GitHub Actions runs.

## 1. Three-version model, no forced numeric alignment

| Domain | Authoritative source inspected | Observed development value | Meaning |
| --- | --- | --- | --- |
| `StudioVersion` | `pyproject.toml` and `apps/windows-studio/src/packlab_studio/__init__.py` | `0.1.0` in both checked-in source declarations | Windows Studio source identity only; not a built or released application |
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

**Null is deliberately a failure/incompleteness marker.** The offline candidate-description validator accepts explicit version/source/artifact/provenance/notice/audit inputs only; it does not inspect or create a binary. A future validated generator must populate exact source/build-provenance facts and fail closed on missing required artifact hashes, source and notices, supported schema range, signing state or independent audit. Even synthetically complete validator input is preparation evidence, not a real release manifest or authorization.

## 2. Changelog policy prepared for PL-0365

Use explicit, reviewed task IDs (e.g., `PL-0350`) and summaries present in a hash-verified source fragment. Cross-check each ID against accepted checkboxes in root `TASKS.md` and a cited `AUDITED_PASS` ChatGPT audit; never use Codex `READY` alone. Reject duplicate/unknown/unaccepted IDs, source-digest mismatches, unsupported summary text, and arbitrary extra fields such as commit-message inferences. Keep private data out. Sort by milestone/task ID into `Added`, `Changed`, `Fixed`, `Security`, `Known limitations`. Cite the source fragment digest and accepted audit; no arbitrary commit-message scraping. No public `CHANGELOG` publication or release tag before PL-0368 owner/M17 gate.

## 3. PL-0366 release checklist, explicit current BLOCKED status

| Required gate | Observed evidence | Current decision |
| --- | --- | --- |
| Windows Installer build + installed offline smoke | PL0350/PL0351 audits PASS; exact accepted warm Installer published privately | ENGINEERING PASS only |
| Private Installer retention | PL0352 artifact `11959245441` until 2026-12-14, readback PASS | TIME-LIMITED, NOT permanent |
| CI protected from private sample datasets | PL0353 V02 audit PASS, five fail-closed upload guards | ENGINEERING PASS |
| iOS Capture simulator all XCTest | Historical October runs remain below; 2026-11-04 hosted runs [41743543561](https://github.com/Sekiph82/PackLab/actions/runs/41743543561) and [41754385597](https://github.com/Sekiph82/PackLab/actions/runs/41754385597) passed 205/205, 0 failed, 0 skipped | **ENGINEERING PASS**; simulator only |
| iOS unsigned device archive / physical install | Not accepted; no validated signed IPA | NOT ACCEPTED |
| Signing credentials / secrets review | Repository is PUBLIC; 2026-11-04 metadata shows zero repository signing secrets and zero configured environments; PL-0358 is `EXTERNAL_PENDING_APPLE_SIGNING_CREDENTIALS` | **EXTERNAL_PENDING**; no signed IPA or device installation verified |
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

## 5. Historical October budget and current authorization

As of **2026-10-15**, the owner reported **USD 56.92** in Actions spending over approximately one week and prohibited new GitHub Actions, retries, paid alternative CI, invoice/payment changes, build artifacts or signing requests through October unless explicitly reauthorized. That historical restriction was superseded by the owner's **2026-11-04** authorization for task-required GitHub Actions and autonomous execution. The current authorization does not permit changing billing settings or spending caps, and it does not make artifact storage guaranteed free. The account billing allowance and actual cost remain unverified; avoid unnecessary runs and do not claim a billing quote or free quota. Any future scope or account/billing change still requires owner authorization.

**References:** `docs/development/NO_ACTIONS_OFFLINE_WORK_POLICY_2026-10-15.md`, `docs/architecture/VERSIONING_POLICY.md`, `docs/packscan/container-layout.md`, `docs/packaging/PL0362_PL0367_OFFLINE_INSTALL_ROLLBACK_PREPARATION.md`, `docs/packaging/GITHUB_ACTIONS_ARTIFACT_RETENTION_POLICY.md`, and `coordination/sessions/M16-C001/PL-0354_CHATGPT_AUDIT_V02.md`.
