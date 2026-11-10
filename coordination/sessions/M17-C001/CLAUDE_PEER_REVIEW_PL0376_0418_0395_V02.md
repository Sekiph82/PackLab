---
coordinationSchema: packlab-coordination/v1
artifactType: claude-peer-review
cycleId: M17-C001
version: 02
actor: CLAUDE_INDEPENDENT_REVIEWER
reviewedCommits:
  - dca8054b952e50a3a4cdcf2d92f3b75f721dfb72  # PL-0376 / PL-0418 / PL-0394 re-review fixes
  - 0e9549bdfd417fd45e858682adc4b3451c12a5a6  # PL-0395 freeze rev 1.0
headAtReview: 731262fac2a2f1b38ba6585723c87fae0379789d
respondsTo:
  - coordination/sessions/M17-C001/CLAUDE_PEER_REVIEW_PL0376_0414_0418_FIXES_V01.md
tasks: [PL-0376, PL-0418, PL-0394 (V03 P3-1 follow-up only), PL-0395]
---

# Independent peer review V02: PL-0376, PL-0418 fixes and first review of PL-0395

I did not implement any of this work. I edited no source, test, tool, doc or tracker file, and I did not commit, push, stash, reset or switch branches. This file is the only file I created in the repository. All probes ran from scratch scripts in the session scratchpad (`rv2_ci.py`, `rv2_copy.py`, `rv2_freeze_mut.py`), against scratch folders or temporary copies of the doc. The scratch folder with junctions and ACL denies was removed afterwards. The concurrent M19 AI-assist review files were not touched.

`git diff 0e9549bd HEAD` and `git diff dca8054b HEAD` over every in-scope file are empty, so `HEAD 731262fa` reviews the same content.

## Commands and results

| Command | Result |
|---|---|
| `pytest -q` on the 6 requested files (`QT_QPA_PLATFORM=offscreen`) | **114 passed** in 75 s |
| `ruff check core apps tools tests` | All checks passed |
| `mypy core apps tools` | Success: no issues found in 288 source files |
| `python -m tools.ci.ci_data_safety --repository . --check-signing-secrets --tracked --check-workflows` | `PACKLAB_CI_DATA_GUARD=PASS`, exit 0 |
| `gh run list --branch main --limit 6` | `731262fa` (contains `dca8054b` and `0e9549bd`): Windows Python Quality run 42889760029 **success**; Signing Material Guard run 42889760013 **success**. The previous four runs are also green. |

## Scope A1: PL-0376, P2-A (unclipped glossy reflections)

What changed:
- The calibration doc gains a "known false pass" limit for unclipped reflections, both bright bands below 240 DN and dark bands (`PL-0375_OBJECT_TEXTURE_CALIBRATION_V01.md:69-75`).
- The doc discloses the extra warnings on labelled glossy packages (lines 76-79).
- The streak row is corrected to ≤ 0.010 and labelled as test-suite data (line 48).
- `test_pl0376_documented_limit_unclipped_dark_reflection_reads_as_texture` pins a 40 DN, 4 px band on plain glossy PET as a texture `pass` (`tests/core/test_object_surface_texture_qa.py:226-235`).
- The algorithm is unchanged.

The numbers match the V01 re-review measurements:
- streak maximum 0.0084 / 0.0100;
- labelled bottle 0.40 → 0.07;
- labelled tube 0.34 → 0.09.

**Judgement against frozen criterion 2** ("Specular limitations do not produce an unsupported reconstruction or physical-accuracy PASS"). The false texture `pass` never becomes an acceptance, a reconstruction PASS or a physical-accuracy PASS. I checked each output in the source:

- **Texture component.** It carries `claim_limit: texture_evidence_only_not_reconstruction_quality` (`core/src/packlab_core/pre_reconstruction_qa.py:772`).
- **Whole QA report.** It is `authority: non_authoritative_capture_qa` and `claim_limit: diagnostic_evidence_only_not_geometry_or_physical_accuracy` (`:792-793`). Its best outcome is `no_automated_concern` with `next_action: continue_workflow_review` (`:814-819`), not a pass.
- **PL-0414 tree.**
  - Its authority is `advisory_only_operator_confirms_every_action` (`core/src/packlab_core/rescan_decision.py:218`).
  - Its best action, rule 7 `proceed_to_reconstruction_review`, is documented as "Continue to reconstruction under human review. This is not an acceptance." (`docs/development/PL-0414_RESCAN_RECAPTURE_DECISION_TREE.md:30`).
  - The tree "never marks a scan as passing or complete" (`:15`).
- **No consumer gates on it.** No Studio or orchestrator code consumes the texture status: the only app consumer is the Qt decode adapter, `apps/windows-studio/src/packlab_studio/pre_reconstruction_qa.py`.
- **V1 boundary doc.** It states that this QA and the tree are advisory, calibrated only on synthetic data, and that a QA "pass" says nothing about reconstruction quality, glossy surfaces included (`V1_LIMITATIONS_AND_MANUFACTURING_BOUNDARY.md:16`).

The remaining risk is that an operator over-reads an advisory signal. That risk is now explicitly disclosed and pinned by a test that fails if the behaviour changes. A single grey view cannot tell a dark reflection from print, so no small algorithm change can close it fully. Disclosure plus routing to human review is the minimum fix that the V01 reviewer accepted. It satisfies criterion 2. **P2-A is closed.**

## Scope A2: PL-0418, P2-B (linked ancestor, unreadable folders)

Code: `tools/dev/scan_copy_manifest.py:38-45`. It checks each ancestor of `abspath(root)` for a symlink or junction, and `os.walk(onerror=_raise)` turns walk errors into `ValueError`. Python is 3.12.10, so `os.path.isjunction` is available.

The probes used real `mklink /J` junctions and real `icacls /deny` ACLs in the scratchpad:

| Probe | Result |
|---|---|
| Identical copy | PASS (`[]`) |
| Root junction / nested junction at depth 1 and depth 2 (V01 probes re-run) | refused |
| `create` from a junction root (CLI) | `ValueError`, no manifest written |
| **Ancestor junction** `jparent\SYN-PKG` → source | **refused** (`root path passes through a symlink or junction`) |
| Grand-ancestor junction `jbase\scans\SYN-PKG` | refused |
| Relative root, with the cwd inside a junctioned folder (`SYN-PKG` and `.`) | refused |
| A genuine copy reached through a junctioned parent | refused (conservative) |
| **8.3 short name**: `C:\...\0AC683~1\...\AVERYL~1\SYN-PK~1`. Here `realpath != abspath`, so the rejected realpath approach would have false-failed. | **PASS** (no false failure) |
| Short form of the scratch base, then `copy1\SYN-PKG` | PASS |
| **Unreadable subfolder** (`icacls /deny RD`, real `PermissionError` 5) at `verify` | `copy_unreadable: unreadable entry: …\captures\deep` |
| The same folder at `create` (API and CLI) | `ValueError`, no manifest written |
| Unreadable copy root (ACL) | `copy_unreadable: unreadable entry` |
| Unreadable **file** (ACL deny on `project.json`) | uncaught `PermissionError`. This fails closed (CLI exit 1 with a traceback). See P3-2. |
| `subst Q:` → source parent, then verify `Q:\SYN-PKG` | PASS. See P3-1. |
| `jparent\..\scans\SYN-PKG` | PASS. This is lexically the source path, the same case as verifying the source itself. |
| Verifying the source itself / an extra empty folder | PASS. Both are known, and both are now disclosed in the doc (SOP step and "Empty folders are not recorded"). |

Hosted CI also passed the new ancestor test on the GitHub Windows runner, whose temp path uses short names. That confirms no false failure there.

Doc accuracy (`docs/development/PL-0418_SCAN_BACKUP_POLICY.md:37-41, 59`):
- "refused … in the copy root, in any folder inside it, and in any ancestor of the root path" is true.
- "Unreadable folders fail instead of being skipped" is true.
- The new SOP sentence ("Run `verify` on the destination machine or medium itself, not on a mapped path …") covers the `subst` and mapped-drive cases that the code cannot detect.
- The test-list bullet matches `tests/ci/test_scan_copy_manifest.py:106-129`.

**P2-B is closed.**

## Scope A3: PL-0394 V03 P3-1 follow-up (`tools/ci/ci_data_safety.py:604`, `sk_` prefix)

Probe `rv2_ci.py` (scratch files):

| File | Result |
|---|---|
| `.yml` `API_TOKEN: some_lower_name` | flagged (previously exempt) |
| `.sh` `export API_TOKEN=lowercase_value` | flagged |
| `.py` `API_TOKEN = sk_live_…` and `Sk_live_…` | flagged |
| `.swift` `API_TOKEN = ghp_…` | flagged |
| `.py` `settings.token` and `some_name` | exempt (as intended) |

The full-repo guard passes. The follow-up is correct.

There is a pre-existing gap, not introduced here: `SECRET_ASSIGNMENT` does not match a bare `API_KEY`, `STRIPE_SECRET_KEY` or `AWS_SECRET_ACCESS_KEY`. The guard is scoped to Apple/GitHub/signing names. P3-5 is informational only.

## Scope B: PL-0395 (first independent review)

### Statements checked against code

| Doc statement (`V1_LIMITATIONS_AND_MANUFACTURING_BOUNDARY.md`) | Code evidence | Verdict |
|---|---|---|
| :13-14 relative / metric-unverified / `mm_unverified` | `ScaleState` = `relative`, `metric-unverified`, `metric-verified` (`reconstruction.py:37-40`). `mm_unverified` is the coordinate unit for metric-unverified (`bounding_dimensions.py:51`, `assembly_*`). M07 dense/mesh refuse `METRIC_VERIFIED` (`reconstruction.py:456`, `mesh_reconstruction.py:238`, `dense_reconstruction.py:177`). Promotion to `metric-verified` requires `accepted_owner_physical` evidence (`calibration/scale_provenance.py:141-146, 319-339`). | True. "Unverified until compared against an independent physical measurement" matches the promotion gate. |
| :16 the QA texture check and the rescan tree are advisory and synthetically calibrated; a "pass" says nothing about reconstruction quality | `pre_reconstruction_qa.py:772, 792-793`; `rescan_decision.py:1, 72, 218`; calibration doc | True |
| :21 the core orchestrator resumes from verified checkpoints (request binding plus output digests) | `reconstruction_orchestrator.py:138, 322-340, 434-448, 496-538` check binding, stage order, verified success, workspace containment and output digests | True |
| :21 Studio does not persist those checkpoints | `apps/windows-studio/src/packlab_studio/reconstruction_execution.py:58` calls `orchestrator.run(request, token)` with no `on_checkpoint` or `resume_from`. No app code calls `RecoveryJournal.checkpoint(...)`. | True |
| :22 device / hosted; :23 Kenya; :17 synthetic; :18 YCB | Consistent with the tracker and CLAUDE.md gates | True |
| :31 no-direct-mold statement; :35-37 acceptance status | Doc-level | Present, unambiguous |

Coverage of the frozen criteria:
1. Capabilities and evidence boundaries: :7-9 ✓
2. Scale, optical/material, reconstruction, editable fit, STEP/export, device, hosting and Kenya gaps: :13-23 ✓
3. No direct mold manufacture and no production authorization: :31 ✓
4. Separate gates:
   - physical measurement: :15, :27, :31;
   - print fit: :20;
   - supplier/material: :20, :27, :31;
   - certification: :3;
   - regulatory: :20, :31;
   - owner decision: :15, :31.
   ✓
5. No synthetic or local result presented as physical or hosted evidence: :9, :17, :22 ✓

I found no overclaims. Every "validated", "accepted" or "certified" is negated or qualified.

### Guard discrimination (`rv2_freeze_mut.py`, temp copies; repo doc untouched)

**Killed:**
- deleting the no-mold sentence;
- "must not" → "may";
- the revision header 1.0 → 1.1;
- removing the 1.0 history row;
- dropping "glossy", "transparent PET", the iPhone 16 sentence or "supplier approval";
- appending "PackLab V1 reconstruction is validated for production packaging."

**Survived:**
- dropping the Kenya bullet ("kenya" still appears in other bullets);
- dropping the advisory-QA sentences;
- dropping, or **inverting**, the "Studio does not persist checkpoints" sentence;
- rewriting the physical-metrology bullet to "software tests are sufficient";
- "It is metric-verified by the marker scale estimate";
- "physically accurate to 0.1 mm";
- "certified and must be used for tooling": the `must` qualifier masks it;
- dropping "Label print fit", "engineering certification" or "explicit owner authorization";
- deleting the Acceptance status section.

So the guard does strongly protect the no-mold statement and the revision marker. The gap list is protected only by keyword presence, and the content of the other gates can regress silently. See P3-3.

## Findings

### P0 / P1 / P2

None.

### P3 (non-blocking)

- **P3-1 (PL-0418).** A `subst` or mapped drive that points at the source still verifies as PASS (`tools/dev/scan_copy_manifest.py:38`). So does a lexical `..` path back to the source. Both are the "verify the source itself" class, and the new SOP sentence covers them (`PL-0418_SCAN_BACKUP_POLICY.md:41`). The ancestor check also refuses legitimate copies behind a junctioned or volume-mount-point folder, which errs toward failure. An optional future hardening would record `st_dev` and the volume serial in the manifest and refuse the same volume.
- **P3-2 (PL-0418).** An unreadable **file** raises an uncaught `PermissionError` (`scan_copy_manifest.py:54`, not converted to `ValueError`). The result is still a fail-closed exit 1, but with a traceback instead of `SCAN_COPY_VERIFY_FAIL`. The module docstring at `:7-8` still says "(including the copy root)" and does not mention ancestors.
- **P3-3 (PL-0395).** The guard checks keywords, not content (survivors listed above). The doc header's claim that the guard "guards … the gap list" (`V1_LIMITATIONS_AND_MANUFACTURING_BOUNDARY.md:3`) is only true for keyword presence. The cheapest discriminating fix is to pin the SHA-256 of the frozen doc body together with its revision row in `tests/ci/test_v1_limitations_freeze.py`. Any edit would then need a new revision row and a hash update, which is the change control the header already promises.
- **P3-4 (PL-0376).** The disclosure lives in a coordination session doc.
  - The operator-facing `PL-0414_RESCAN_RECAPTURE_DECISION_TREE.md:30` (rule 7) and the `PL-0400_OPERATOR_CAPTURE_CHECKLIST.md` do not carry the glossy/transparent "texture pass is not print evidence" caveat, although the calibration doc (`:75`) refers to PL-0400 for it.
  - Two calibration-doc sentences now read too strongly next to the new limit: `:52` "A labelled PET bottle beside a highlight still passes", which holds only for one streak on the bottle, and `:80` "The specular guard prevents false texture", which holds only for clipped highlights ≥ 240 DN.
  - The pinned test covers the dark band only, not the 239 DN bright band.
- **P3-5 (PL-0394, pre-existing, informational).** `SECRET_ASSIGNMENT` (`tools/ci/ci_data_safety.py:131-139`) does not match bare `API_KEY`, `*_SECRET_KEY` or `*_SECRET_ACCESS_KEY` names. It is out of scope for this follow-up.
- **P3-6 (PL-0395).** The 1.0 revision row says "Independent Claude peer review pending" (`:44`). Recording this review there is itself a doc change, which by `:3` needs a revision entry. Either record the review in the tracker only, or add a 1.0.1 row.

## Verdicts

| Task | Verdict | Basis |
|---|---|---|
| PL-0376 | **PASS (CLAUDE_PEER_AUDITED_PASS-eligible)** | P2-A is closed by an explicit known-false-pass disclosure and a pinned test. The source confirms that the texture `pass` and PL-0414 `proceed_to_reconstruction_review` are advisory and non-authoritative, and that nothing gates on them, so criterion 2 holds: no reconstruction or physical-accuracy PASS is produced. Only P3-4 remains. |
| PL-0418 | **PASS (CLAUDE_PEER_AUDITED_PASS-eligible)** | P2-B is closed. Real junction and ACL probes confirm refusal of ancestor and nested junctions and of unreadable folders. 8.3 short-name paths do not false-fail, locally or on the hosted runner. The doc is accurate, and the SOP covers mapped and `subst` paths. P3-1 and P3-2 remain. |
| PL-0394 (V03 P3-1 follow-up only) | Correct | Lower-case exemption limited to `.py` and `.swift`; `sk_` is flagged; the full-repo guard passes. |
| PL-0395 | **PASS (CLAUDE_PEER_AUDITED_PASS-eligible)** | Every doc statement checked against the code is true, including checkpoint resume (core yes, Studio no), the scale vocabulary and the advisory QA. All 5 criteria are covered and there are no overclaims. The guard reliably protects the no-mold statement and the revision. The gap-list guard is only keyword-level (P3-3, recommended). |

Hosted CI for `731262fa` is green. Nothing here is physical, factory, Kenya, iPhone or real-capture validation. Every fixture and probe is synthetic, and those gates stay open.
