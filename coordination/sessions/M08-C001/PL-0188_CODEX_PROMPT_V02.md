# PL-0188 - Codex Work Order V02

Task: **Add manual mask-correction UI and versioned revision handoff**

Repository:
https://github.com/Sekiph82/PackLab

Branch:
`main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CHATGPT_AUDIT_V02.md

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/segmentation.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/mask_postprocessing.py
- https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md
- https://github.com/Sekiph82/PackLab/blob/main/apps/windows-studio/src/packlab_studio/shell.py
- https://github.com/Sekiph82/PackLab/blob/main/apps/windows-studio/src/packlab_studio/viewport.py

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0188_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0188_CODEX_LOG_V02.md

## Authorization gate

Before material work:

1. `git fetch origin main --prune`
2. inspect `git status --porcelain`
3. inspect `git rev-list --left-right --count HEAD...origin/main`
4. fast-forward only when safe

The live tracker must authorize:
- Current Milestone: M08
- Current Sprint: M08-C001
- Current Task: PL-0188 V02
- Current Task Status: READY
- Required Actor: CODEX
- PL-0187 independently accepted
- PL-0189+ and M09 unauthorized

Otherwise stop `TASK_STATE_MISMATCH`.

Do not edit `TASKS.md`, owner ADRs, ChatGPT audits/criteria, accepted predecessor evidence or later-task files.

## Frozen scope

Implement:

1. a PackLab-owned domain service for manual mask correction;
2. the minimum Windows Studio presentation seam required to view/edit a mask and submit or cancel a correction.

The UI is presentation only. It may render and collect user intent, but it must not own authoritative mask/revision identity, provenance, ancestry, invalidation or source bytes.

Do not implement PL-0189 invalidation orchestration.

## Domain correction contract

Input:

- valid parent `MaskArtifact` with in-memory raster;
- explicit editor identity;
- canonical bounded edit operations;
- correction pipeline/version.

Output:

- a new immutable child `MaskArtifact` revision.

Before using parent raster bytes, enforce:

```python
parent.raster.digest == parent.mask_digest
```

or route through a shared verified accessor with equivalent semantics.

Never mutate parent mask/raster or source image bytes.

## Edit operations

Define a deterministic, minimal edit operation model.

At minimum support explicit pixel-domain correction semantics equivalent to:

- set/paint foreground;
- erase/set background.

You may choose single pixels or bounded strokes/runs if the representation remains deterministic, canonical and testable.

Requirements:

- source/mask grid coordinates only;
- no resizing/resampling;
- integer coordinate validation;
- out-of-bounds rejection;
- no bool-as-int ambiguity;
- malformed operation rejection;
- deterministic operation ordering;
- explicit behavior when multiple edits touch the same pixel.

Do not hide smoothing, post-processing or model reruns inside manual editing.

## Editor provenance

Editor identity must be explicit input, validated and normalized.

Record sufficient provenance to distinguish:
- who/what submitted the correction;
- parent revision;
- correction pipeline/version;
- canonical edit identity or resulting corrected mask identity.

Do not infer editor identity from OS username, machine name, environment variables, email/account data or other ambient/private context.

Use a caller-supplied non-secret editor label/ID with safe validation.

## Child identity and ancestry

The child must preserve:

- source image asset ID/digest;
- dimensions and transform;
- existing segmentation/model provenance;
- prior manual ancestry;
- parent revision;
- parent digest.

The new manual correction revision identity must be deterministic.

Identity-bearing inputs must not include wall-clock timestamp.

A reasonable identity input set is:

```text
parent artifact/revision/digest
source asset/digest/dimensions/transform
manual correction pipeline ID/version
validated editor ID
canonical normalized edit operations
output mask digest
```

Append manual ancestry rather than replacing it.

Do not overwrite raw or post-processed parent artifacts.

## No-op and cancellation behavior

Differentiate:
- presentation cancel/reject: no authoritative child created;
- submitted edits that change pixels: produce a child revision;
- submitted canonical no-op: define one explicit safe policy and test it.

Preferred safe policy: reject no-op authoritative submissions rather than manufacturing meaningless revisions.

## Windows Studio seam

Add only the minimum UI/presentation pieces required by this task.

Prefer existing PackLab shell/viewport architecture rather than creating a competing window/application framework.

The UI may:
- display source/mask overlay;
- switch between foreground/background edit mode;
- collect bounded edit commands;
- submit;
- cancel/undo unsubmitted session edits.

The UI must delegate authoritative revision creation to the domain service.

Keep native/manual visual acceptance claims bounded. Automated headless/offscreen or presentation-adapter tests are evidence, not a claim that a human visually approved every interaction.

## Tests

Add focused tests for:

- correction service works without UI/display;
- matching parent raster/digest accepted;
- mismatched parent raster/digest rejected before correction;
- paint/set foreground;
- erase/set background;
- malformed/out-of-bounds edit rejection;
- deterministic operation normalization/order semantics;
- deterministic child digest/revision;
- parent/source immutability;
- editor validation and provenance;
- ancestry append behavior across repeated corrections;
- no-op submission policy;
- cancel/reject creates no child;
- UI delegates to domain service and does not compute authoritative IDs;
- headless/offscreen composition where available;
- PL-0186 and PL-0187 regressions.

Use public/synthetic fixtures only.

## Allowed change boundary

- new PackLab-owned core manual-mask correction module/service;
- minimal extensions to existing segmentation contracts only if required and backward-compatible;
- minimum Windows Studio presentation seam;
- dedicated tests;
- required V02 log.

Do not add dependencies unless already reviewed and truly necessary. Prefer existing PySide6.

Do not add hosted APIs, model/checkpoint downloads, private scans, generated reconstruction media, signing material or later-task code.

## Validation

Run:

- PL-0188 focused tests;
- PL-0186/PL-0187 relevant regressions;
- exact locked full pytest suite;
- Ruff;
- format check;
- targeted/relevant mypy;
- compileall;
- `git diff --check`;
- protected-file/scope review;
- dependency/license review;
- privacy/secrets/signing review;
- generated/binary review;
- remote visibility/freshness checks.

Report unrelated pre-existing debt without changing unrelated files.

## Publication

Create separate commits:

1. implementation/evidence commit(s);
2. log-only commit:
   https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0188_CODEX_LOG_V02.md

The log must include:

- synchronized starting SHA;
- implementation SHA(s);
- exact domain correction API;
- edit operation semantics;
- editor provenance rules;
- child revision/ancestry identity;
- UI/domain ownership boundary;
- focused/full/static results;
- changed files;
- native/headless limitations;
- explicit statement that PL-0189+ and M09 were not started.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Stop. Independent ChatGPT audit is required before PL-0189.
