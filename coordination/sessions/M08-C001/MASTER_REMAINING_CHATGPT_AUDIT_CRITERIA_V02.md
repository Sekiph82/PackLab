# M08-C001 - Remaining Batch Master ChatGPT Audit Criteria V02

Milestone: **M08 - Segmentation, Object Extraction & Reconstruction QA**
Accepted frozen children: **PL-0184 through PL-0187**
Remaining batch: **PL-0188 through PL-0201**

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/MASTER_REMAINING_CODEX_PROMPT_V02.md

Required master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/MASTER_REMAINING_CODEX_LOG_V02.md

All criteria are mandatory.

1. Live `TASKS.md` authorizes M08-C001 / remaining batch PL-0188 through PL-0201 / READY / CODEX before implementation.
2. PL-0184 through PL-0187 remain frozen `AUDITED_PASS`; their accepted architecture, contracts and evidence are not rewritten by later children.
3. Codex executes PL-0188 through PL-0201 exactly in order.
4. A validation-green child publishes its implementation/evidence commit and separate log-only commit, verifies remote visibility, then continues directly to the next child without waiting for an intermediate ChatGPT audit.
5. A child log ending `READY_FOR_INDEPENDENT_AUDIT` is an evidence/publication boundary, not a batch pause condition.
6. Codex stops the batch only for a real failed/blocked/owner-required condition, tracker/branch mismatch, unresolved license/privacy/security issue, missing mandatory capability/pre-read, or need to start M09/later work.
7. PL-0188 keeps correction truth in PackLab domain services; UI is presentation only, parent raster/digest integrity is verified, manual ancestry/editor provenance are explicit, and cancel/no-op behavior does not fabricate revisions.
8. PL-0189 publishes immutable independent mask revisions, preserves ancestry, rejects duplicate/ambiguous revision state, and invalidates or marks stale any downstream object geometry bound to an older mask revision.
9. PL-0190 follows the mandatory object-mask lifting architecture: synthetic convention gate, normalized camera convention, visibility before mask voting, bounded deterministic support evidence, correct invalidation parents, `generated=false`, and `OBJECT_CAPTURE_GEOMETRY` authority only.
10. PL-0191 creates deterministic review overlays/contact sheets as derived QA evidence without changing source or mask authority.
11. PL-0192 through PL-0199 implement explainable, versioned, provenance-bound QA diagnostics for capture/reconstruction quality with explicit thresholds and missing-data behavior; no black-box or physical-accuracy claim is introduced.
12. PL-0200 is fail-closed and rejects AI_VISUAL_REFERENCE/generated/missing-provenance geometry as a substitute for accepted captured geometry.
13. PL-0201 produces bounded evidence-linked recapture suggestions and a full-rescan fallback only when evidence warrants it.
14. RAW_CAPTURE/source bytes remain immutable across the entire remaining batch.
15. Masks remain derived mask authority. M08 never promotes to SCAN_MASTER, metric verification or CAD authority.
16. Any consumer deriving new content from an in-memory mask raster verifies its bytes against the declared parent mask digest or uses an equivalent accepted verified-accessor boundary.
17. No unreviewed model/runtime/checkpoint, hosted service, dependency, private scan, signing material or unsafe generated artifact is introduced.
18. Each child has focused success/negative/boundary/regression tests, exact locked full-suite evidence, changed-file static checks, scope/protected-file review, dependency/license/privacy/generated/binary review and remote visibility evidence.
19. Every child keeps a separate implementation/evidence commit and separate child-log-only commit.
20. Every child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.
21. The master log indexes every child with exact prompt/criteria/log URLs, implementation SHA(s), log SHA, focused/full results, limitations and final frontier.
22. If the batch stops early, the master log records `BATCH_STOPPED`, the exact stopping child/reason, and retained earlier green evidence.
23. If PL-0201 completes green, the master log records `BATCH_COMPLETED` and ends exactly `AWAITING_MILESTONE_AUDIT`.
24. Codex does not edit `TASKS.md`, owner ADRs or ChatGPT audit/criteria artifacts during implementation.
25. M09 and later work remain unauthorized.

After the batch handoff, ChatGPT performs fresh independent audits of the child outputs and then the M08 milestone audit. Builder validation is not audit acceptance.
