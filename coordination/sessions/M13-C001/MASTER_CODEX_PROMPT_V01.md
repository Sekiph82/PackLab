# M13-C001 - Codex Master Work Order V01

Milestone: **M13 - CAD/BREP & Engineering Export**
Ordered children: **PL-0289 through PL-0309**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

Required master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_LOG_V01.md

Accepted predecessor:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/M12-C001_CHATGPT_AUDIT_V01.md

Standalone/captured Design Model authority:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0005-standalone-design-geometry-root.md

Physical-validation deferral:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/M09_PHYSICAL_VALIDATION_DEFERRAL_OWNER_DECISION_V01.md

Dependency/license register:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/DEPENDENCY_LICENSE_REGISTER.md

## Continuous batch rule

Execute PL-0289 through PL-0309 in exact order as one continuous Codex batch.

For every green child:

1. fetch/synchronize safely and preserve owner-local work;
2. read master + child prompt/criteria + mandatory pre-reads;
3. implement only the current child;
4. run focused/predecessor/full/static/scope/security/dependency checks;
5. publish implementation/evidence commit(s);
6. publish a separate child-log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`;
7. verify remote visibility;
8. update the master child table with exact SHAs/results;
9. continue directly to the next child.

Do not pause for intermediate ChatGPT audit.

## PL-0289 binding gate

No Python OpenCascade binding is preselected.

PL-0289 must select the binding from actual Windows x86-64 / CPython 3.12 / uv evidence. Candidate examples may include pip/uv-capable OCP packages and pythonocc-core where feasible, but package names are not approval.

Selection requires:

- successful install and import in the real PackLab environment;
- exact binding package/version/build;
- observed OCCT/kernel version;
- required capability smoke for BREP/revolve/loft/boolean/tessellation/STEP;
- exact lockfile resolution;
- wheel/native artifact provenance/digests where practical;
- binding license evidence distinct from OCCT license/exception;
- transitive/native redistribution attention;
- no runtime package/binary auto-download.

If no reviewed candidate passes, stop `BLOCKED_OPEN_CASCADE_BINDING`.

Only PL-0289 may add/select the CAD binding dependency. Later children consume the accepted binding through PackLab's CAD adapter.

## CAD authority model

M13 adds a derived CAD representation layer:

```text
CAPTURED_SCAN_MASTER or STANDALONE_DESIGN_GEOMETRY
  -> DESIGN_MODEL
  -> CAD/BREP representation
  -> engineering exports / technical drawings
```

Hard rules:

- Scan Master remains immutable captured authority.
- Design Model remains editable parametric authority.
- CAD/BREP is derived engineering representation, not replacement Design Model truth.
- PREVIEW_PROXY/tessellation remains derived/disposable.
- Named CAD subshape references are best-effort lineage mappings, never universal topological identity claims.
- Both CAPTURED_SCAN_MASTER and STANDALONE_DESIGN_GEOMETRY Design Models are supported where geometrically applicable.
- Captured-only services continue to reject standalone inputs where captured evidence is inherently required.

## Unit and physical-validation rules

PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`.

Therefore:

- `RELATIVE / reconstruction_units` must never silently become millimetres;
- `METRIC_UNVERIFIED / mm_unverified` may be encoded numerically as millimetres for STEP/STL/drawings only when the child contract explicitly allows it;
- encoding mm units does not mean a physical object was measured accurately;
- topology-valid BREP, successful STEP round-trip, printable STL or dimensionally self-consistent drawing does **not** authorize mold/manufacturing/certification claims;
- every export/drawing manifest/title block must retain the source authority and unverified physical status.

### Format-specific unit policy

- STEP printable/engineering export: require `mm_unverified`; reject RELATIVE unless a separately authorized explicit conversion exists.
- Printable STL: require `mm_unverified`; STL unit ambiguity must be covered by mandatory manifest/sidecar.
- OBJ/GLB: may support RELATIVE or mm_unverified if unit/scale transforms are explicit and reversible in metadata.
- Drawings: RELATIVE must be labeled reconstruction-relative; mm_unverified may display numerical mm only with explicit unverified disclaimer.

## Ordered child package

1. **PL-0289** — Benchmark/select supported Python OpenCascade binding for Windows packaging.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0289_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0289_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0289_CODEX_LOG_V01.md

2. **PL-0290** — Implement CAD capability adapter and version diagnostics.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0290_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0290_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0290_CODEX_LOG_V01.md

3. **PL-0291** — Convert profile/revolve Design Models into OpenCascade BREP solids.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0291_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0291_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0291_CODEX_LOG_V01.md

4. **PL-0292** — Convert lofted cross-section Design Models into BREP solids.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0292_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0292_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0292_CODEX_LOG_V01.md

5. **PL-0293** — Implement boolean feature support needed for handle openings and simple indentations.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0293_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0293_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0293_CODEX_LOG_V01.md

6. **PL-0294** — Validate solid topology and report non-manifold/invalid BREP failures.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0294_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0294_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0294_CODEX_LOG_V01.md

7. **PL-0295** — Preserve named feature references where practical across regeneration.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0295_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0295_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0295_CODEX_LOG_V01.md

8. **PL-0296** — Tessellate BREP back to preview mesh with controlled tolerance.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0296_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0296_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0296_CODEX_LOG_V01.md

9. **PL-0297** — Export Design Model/assembly to STEP with millimetre units.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0297_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0297_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0297_CODEX_LOG_V01.md

10. **PL-0298** — Export printable STL with explicit unit handling and mesh-quality options.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0298_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0298_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0298_CODEX_LOG_V01.md

11. **PL-0299** — Export OBJ and GLB from Design Model with part naming.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0299_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0299_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0299_CODEX_LOG_V01.md

12. **PL-0300** — Add export manifest recording source project, revision, scale and software versions.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0300_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0300_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0300_CODEX_LOG_V01.md

13. **PL-0301** — Add round-trip validation that reopens exported STEP and rechecks bounding dimensions.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0301_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0301_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0301_CODEX_LOG_V01.md

14. **PL-0302** — Add export UI with clear distinction between Scan Mesh and editable Design Model.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0302_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0302_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0302_CODEX_LOG_V01.md

15. **PL-0303** — Generate front/side/top orthographic views from Design Model.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0303_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0303_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0303_CODEX_LOG_V01.md

16. **PL-0304** — Generate section views at user-selected heights/planes.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0304_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0304_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0304_CODEX_LOG_V01.md

17. **PL-0305** — Add dimension annotations for overall H/W/D, neck and selected features.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0305_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0305_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0305_CODEX_LOG_V01.md

18. **PL-0306** — Add title block with package ID, revision, units and disclaimer.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0306_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0306_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0306_CODEX_LOG_V01.md

19. **PL-0307** — Export drawing to SVG and DXF.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0307_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0307_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0307_CODEX_LOG_V01.md

20. **PL-0308** — Export PDF drawing if a stable PDF path is available without compromising vector source.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0308_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0308_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0308_CODEX_LOG_V01.md

21. **PL-0309** — Validate drawing dimensions against Design Model numerical values.
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0309_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0309_CHATGPT_AUDIT_CRITERIA_V01.md
   Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0309_CODEX_LOG_V01.md

## Technical drawing rules

- Shared vector drawing model is source truth.
- Orthographic/section/dimension values derive from Design Model/CAD numerical geometry, never rendered pixels.
- SVG/DXF are vector exports of the shared drawing model.
- PDF is presentation export only and must not replace vector source.
- PL-0308 may reuse an already-reviewed stable vector PDF path. If a new dependency is required, stop for dependency review rather than silently adding it.
- Drawing numerical consistency checks are software validation, not physical metrology.

## Stop conditions

Stop the batch on:

- no acceptable Python OpenCascade binding;
- child validation failure not correctable within frozen scope;
- CAD/kernel capability mismatch;
- license/dependency/privacy/security issue;
- tracker/synchronization conflict;
- physical-authority ambiguity;
- PL-0308 requiring an unreviewed new PDF dependency;
- owner-required decision;
- need to start M14 or later work.

On stop:

1. publish current child blocker/evidence log;
2. update master status `BATCH_STOPPED`;
3. record exact child/reason;
4. preserve all prior green child evidence;
5. end master log exactly `AWAITING_MILESTONE_AUDIT`;
6. stop.

## Successful handoff

After PL-0309 completes green:

1. ensure all 21 rows are populated;
2. set master status `BATCH_COMPLETED`;
3. record final local/origin/GitHub `main` SHA and clean execution worktree;
4. confirm M14 was not started;
5. publish final master-log-only commit;
6. end exactly:

`AWAITING_MILESTONE_AUDIT`
