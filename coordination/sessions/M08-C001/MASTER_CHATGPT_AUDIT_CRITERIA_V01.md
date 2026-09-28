# M08-C001 - Master ChatGPT Audit Criteria V01

Milestone: **M08 - Segmentation, Object Extraction & Reconstruction QA**
Scope: **PL-0184 through PL-0201**
All criteria are mandatory.

1. Root `TASKS.md` explicitly authorizes `M08-C001 / READY / CODEX` for this
   exact batch before implementation; M07 is `AUDITED_PASS`, PL-0068 remains
   `OWNER_REQUIRED`, and M09 remains unauthorized.
2. The package contains this master criteria, the master prompt, the required
   master-log template, and one prompt/criteria/log path for each ordered child.
3. Codex executes exactly PL-0184 through PL-0201 in order, with distinct
   implementation/evidence and log-only boundaries, exact child handoffs, and
   no later-child acceptance after a failed or blocked frontier.
4. PL-0184 defines replaceable PackLab-owned segmentation, capability,
   request/result, mask-artifact and mask-revision contracts with complete
   coordinate, source, model, prompt, transform and provenance data.
5. PL-0185 supplies reproducible public/synthetic benchmark evidence and an
   explicit model-selection decision without treating reference code, model
   availability, or visual similarity as commercial/production authority.
6. PL-0186 implements only the explicitly selected, license-cleared backend
   behind PL-0184, with capability probing, fail-closed unavailable behavior,
   no automatic downloads, and source immutability.
7. PL-0187 implements deterministic, versioned post-processing with bounded
   hole/edge/component behavior, preserving parent provenance and mask revision.
8. PL-0188 provides manual correction through a presentation seam while
   keeping mask truth and revision/provenance in domain services; native UI
   acceptance is not fabricated.
9. PL-0189 versions masks independently, preserves manual ancestry, detects
   duplicate/ambiguous revisions, and invalidates downstream object geometry
   when the mask revision changes.
10. PL-0190 implements convention-gated, visibility-aware multiview lifting,
    deterministic support voting, threshold/profile provenance, conservative
    cleanup, preliminary OBB, inherited scale, `generated=false`,
    `OBJECT_CAPTURE_GEOMETRY`, and complete invalidation dependencies.
11. PL-0191 produces truthful mask-quality overlays/contact sheets without
    changing source or mask authority.
12. PL-0192 through PL-0199 implement explainable, deterministic QA metrics
    for capture quality, duplicates, lens consistency, registration, sparse
    connectivity, dense/object coverage, artifacts and confidence; no black
    box, metric, or Scan Master claim is introduced.
13. PL-0200 gates downstream parametric fitting on captured-geometry evidence,
    and explicitly rejects `AI_VISUAL_REFERENCE` as a substitute.
14. PL-0201 produces bounded, evidence-linked recapture sectors rather than
    silently demanding a full rescan or changing source data.
15. Public tests cover success, missing/invalid capability, coordinate and
    resize transforms, source immutability, revision invalidation, projection
    and occlusion boundaries, iteration determinism, QA thresholds, unsafe
    inputs, AI authority isolation and regression behavior.
16. The exact locked full suite exits `0`; no new skip/xfail hides a finding.
    Environment, model-license, native/device, physical, and owner gates are
    reported truthfully.
17. Ruff, format, targeted/relevant mypy, compileall, `git diff --check`,
    protected-file/scope, dependency/lock/license, privacy/secrets/signing,
    generated/binary and remote-visibility checks pass truthfully.
18. Every child log and the master log contain full GitHub URLs, exact SHAs,
    commands/results, expected/failure conditions, limitations, scope/privacy
    review and correct handoff markers. The master log ends exactly
    `AWAITING_MILESTONE_AUDIT`.
19. No child edits `TASKS.md`, writes a ChatGPT audit, starts M09/later work,
    adds an unreviewed model/runtime, changes RAW_CAPTURE, claims native/
    physical/owner acceptance, or publishes private/confidential data.

Closure requires a fresh independent ChatGPT audit for every child and then a
separate milestone audit. Builder validation is not acceptance.
