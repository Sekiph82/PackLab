# M08-C001 - Codex Master Work Order V01

Milestone: **M08 - Segmentation, Object Extraction & Reconstruction QA**
Ordered children: **PL-0184 through PL-0201**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

This prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/MASTER_CODEX_PROMPT_V01.md

Master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

Required master log template:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/MASTER_CODEX_LOG_V01.md

Accepted predecessor:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/M07-C002_CHATGPT_AUDIT_V01.md

## Authorization and synchronization

Before material work, live `TASKS.md` must explicitly authorize `M08-C001`,
`READY`, `CODEX`, and this exact ordered batch. It must record the complete
package URLs on `origin/main`, preserve M07 as `AUDITED_PASS`, preserve
PL-0068 as `OWNER_REQUIRED`, and keep M09 and later work unauthorized. If the
tracker, branch, package, or active prompt does not match, stop with
`TASK_STATE_MISMATCH`.

At the start of the batch and before every child:

1. confirm the Git root is `C:\Users\sekip\Desktop\PackLab`;
2. confirm `origin` is `https://github.com/Sekiph82/PackLab.git` and branch is `main`;
3. run `git fetch origin main --prune`;
4. compare `HEAD...origin/main` and fast-forward only when clean and behind-only;
5. preserve owner/local work; never reset, clean, stash, rebase, force-push,
   destructive-checkout, or overwrite unrelated files.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, M07
architecture/ADR-0003 and accepted M07 audits, the matching child prompt and
criteria, and every mandatory pre-read before that child. PL-0184 must read
`docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md` in full.
PL-0190 must read both that file and
`docs/implementation/PL-0190_OBJECT_MASK_LIFT_MULTIVIEW_FUSION.md` in full.

## Exact child order and handoffs

Execute only this order. Each child has a separate implementation/evidence
boundary and separate log-only publication boundary. A child ends with
`READY_FOR_INDEPENDENT_AUDIT`; the master log ends with
`AWAITING_MILESTONE_AUDIT`.

1. PL-0184 - replaceable segmentation backend and mask/provenance contracts
2. PL-0185 - public/synthetic segmentation benchmark and model-selection evidence
3. PL-0186 - selected license-cleared local PyTorch segmentation backend
4. PL-0187 - deterministic mask post-processing
5. PL-0188 - manual mask-correction UI and revision handoff
6. PL-0189 - independent mask revisions and downstream invalidation
7. PL-0190 - multiview mask-to-3D lifting and OBJECT_CAPTURE_GEOMETRY
8. PL-0191 - mask-quality overlays and contact-sheet review
9. PL-0192 - pre-reconstruction image/reconstruction QA report
10. PL-0193 - duplicate and near-duplicate photo detection
11. PL-0194 - focal/lens consistency warnings
12. PL-0195 - registered-photo ratio
13. PL-0196 - sparse-cloud connectivity and fragmentation indicators
14. PL-0197 - dense/object coverage and multiview support indicators
15. PL-0198 - reconstruction artifact and floating-component detection
16. PL-0199 - explainable reconstruction confidence
17. PL-0200 - downstream parametric-fit quality gate
18. PL-0201 - targeted recapture-sector suggestions

The full prompt/criteria/log URL for every child is listed in the matching
child files and must be indexed in the master log. Do not skip a child or
continue past a failed/blocked child.

## Architecture and scope boundary

Keep PackLab-owned, backend-neutral segmentation and object-extraction
authority. Masks are derived, revisioned artifacts; RAW_CAPTURE photos and
metadata remain immutable. All masks record source image identity/digest,
dimensions, top-left origin, pixel convention, resize/transform provenance,
backend/model/checkpoint/runtime provenance, prompt data, confidence where
available, post-processing version, timestamp, revision and manual ancestry.

M08 may use public or synthetic data and an explicitly reviewed,
license-cleared local runtime. It must not silently select SAM 3, VGGT,
TRELLIS, a checkpoint, a hosted API, or any model/runtime whose license,
hash, provenance and deployment path are not explicit. Do not automatically
download/install models or engines. OpenReality is architecture reference,
not a PackLab dependency or authority.

Object extraction must preserve the authority hierarchy:
`RAW_CAPTURE -> RECONSTRUCTION_OBSERVATION -> OBJECT_CAPTURE_GEOMETRY`.
M08 must not create `SCAN_MASTER`, claim metric verification, perform M10
cleanup/promotion, or convert `AI_VISUAL_REFERENCE` into captured geometry.
PL-0190 must normalize camera convention after a synthetic known-point gate,
perform visibility before mask voting, persist bounded aggregate vote evidence,
inherit scale limitations, set `generated=false`, and invalidate on any
parent/revision/convention/policy change.

Use existing project-layout, provenance, workspace, reconstruction, source
immutability, and job authorities. Keep UI presentation separate from
contract truth. Do not add private scans, supplier material, credentials,
signing material, unsafe generated geometry, dependency/lock changes outside
an explicitly audited and license-cleared child, or M09/later implementation.

## Evidence and commit rules

For every child, record exact commands, expected results, explicit failure
conditions, actual results, exit status, negative/boundary/regression tests,
changed files, protected-file review, dependency/license/privacy review,
limitations, and remote visibility. Use one implementation/evidence commit
followed by a separate child-log-only commit. Do not predeclare a future log
commit SHA. The master log must index every child, implementation SHA,
log-only SHA, full GitHub URLs, test results, limitations and frontier.

Required checks include focused behavior-sensitive tests, relevant M07
regressions, the exact locked full pytest suite, Ruff/format, targeted mypy,
compileall, `git diff --check`, protected-file/scope checks, dependency/lock
and license checks, privacy/secrets/signing checks, generated/binary checks,
and remote visibility. Native UI/device, physical packaging, and owner-only
acceptance are reported as unavailable or pending; never claimed as passed.

## Stop conditions

Stop the entire batch at the current child on tracker/branch/synchronization
mismatch, a frozen validation failure not correctable within that child,
architecture/specification conflict, missing mandatory pre-read, unresolved
model/checkpoint license or dependency decision, source/provenance/invalidation
failure, privacy/security issue, owner/native/manual gate, unavailable required
capability, or any need to start M09/later work. Write the current child log
and master log with the exact frontier, `BATCH_STOPPED`, retained earlier
evidence, and final `AWAITING_MILESTONE_AUDIT`.

## Final handoff

After PL-0201 is validation-green and its log is remotely visible, complete
the master log with `BATCH_COMPLETED`, publish it as a separate master-log-only
commit, verify `origin/main`, return `AWAITING_MILESTONE_AUDIT`, and stop. Do
not start M09 or any later task.
