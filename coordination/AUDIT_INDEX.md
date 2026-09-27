# PackLab Audit Index

> ChatGPT-owned reusable audit memory. This file is **not** live project state. Root `TASKS.md` remains the only H!veAI/current-status authority.

## Learning format

Each reusable finding uses a permanent `AL-PL-xxxx` ID and records:

- affected subsystem/task family;
- failure mode;
- why prior evidence could miss it;
- required future prompt/test/audit behavior;
- originating cycle/audit link.

## Active audit learnings

### AL-PL-0001 — GitHub-first authority

**Applies to:** all PackLab work.

**Finding:** Local workspace state must never silently override GitHub `main` project truth.

**Required behavior:** Codex verifies repository identity and synchronization before implementation. The first owner-authorized bootstrap treats GitHub as authoritative; later sessions stop on unexpected divergence unless the owner explicitly authorizes replacement.

**Origin:** PackLab coordination architecture initialization.

### AL-PL-0002 — Single H!veAI tracker

**Applies to:** all task lifecycle changes.

**Finding:** Duplicating current task/progress/actor in logs, handoff files or coordination indexes creates drift.

**Required behavior:** only root `TASKS.md` carries live H!veAI state. ChatGPT is the sole writer of lifecycle/progress/task closure. Session artifacts are evidence only.

**Origin:** PackLab coordination architecture initialization.

### AL-PL-0003 — Implementer tests are correlated evidence

**Applies to:** all code, CV, geometry, CI and device tasks.

**Finding:** Codex can write implementation and tests using the same wrong assumption, so a green suite alone cannot establish independent closure.

**Required behavior:** ChatGPT audits actual source/diff and test sensitivity, exercises negative/boundary reasoning, and explicitly labels runtime checks it could not independently rerun.

**Origin:** PackLab strict audit policy.

### AL-PL-0004 — Scan Mesh is not Design Model

**Applies to:** reconstruction, mesh, parametric and CAD tasks.

**Finding:** A clean triangle mesh can look editable while still failing PackLab's dimension-driven design objective.

**Required behavior:** audits must verify that editable geometry is parameter-driven and distinct from immutable/reference scan assets before closing parametric/CAD tasks.

**Origin:** PackLab architecture contract.

### AL-PL-0005 — Physical accuracy needs physical evidence

**Applies to:** calibration, measurement, reconstruction accuracy and engineering export.

**Finding:** visual similarity or self-consistent software output is not proof of real-world dimensional accuracy.

**Required behavior:** criteria must require known dimensions, units, tolerance and provenance; owner/device/caliper evidence is E4/E1 where independent runtime reproduction is unavailable.

**Origin:** PackLab architecture contract.

### AL-PL-0006 — Review newly created untracked files with a diff that can see them

**Applies to:** documentation, schema, source and test tasks that create new files.

**Finding:** plain `git diff -- <path>` returns no content for a brand-new untracked file, so a prompt can appear to request a meaningful pre-commit review while the command is actually blind to the new file.

**Required behavior:** when a task creates a new file, prompts should require one of: `git add -N <path>` then `git diff -- <path>`, deliberate staging followed by `git diff --cached`, or another explicit content-review command. The audit must not treat an empty unstaged diff of an untracked file as proof of content review.

**Origin:** `PL-0002-C001 / CHATGPT_AUDIT_V01.md`.

### AL-PL-0007 — Do not self-reference the future log commit SHA

**Applies to:** all Codex implementation logs.

**Finding:** a `CODEX_LOG_VNN.md` file cannot truthfully contain the SHA of the commit that contains that same final log content before that commit exists. Treating a pre-log implementation SHA as `finalCommit` creates misleading metadata even when the actual GitHub ancestry is correct.

**Required behavior:** Codex logs should record the synchronized starting commit and the implementation commit. They should not predeclare the future log-containing commit SHA. ChatGPT records the actual log commit / audited head from GitHub in the independent audit artifact after the log is pushed.

**Origin:** `PL-0003-C001 / CHATGPT_AUDIT_V01.md`.

### AL-PL-0008 — Integrated GPU AdapterRAM is not dedicated VRAM

**Applies to:** Windows diagnostics, capability probing, performance planning, CUDA/GPU decisions.

**Finding:** `Win32_VideoController.AdapterRAM` can report a memory field for integrated graphics that does not represent dedicated VRAM and does not establish CUDA capability.

**Required behavior:** diagnostics may record the field with provenance, but must label it as reported/possibly shared for integrated GPUs. CUDA support must be detected independently from actual GPU/vendor/runtime capability, and performance requirements must not be inferred from the CIM AdapterRAM field alone.

**Origin:** `PL-0004-C001 / CHATGPT_AUDIT_V01.md`.

### AL-PL-0009 — Governance cross-links must be semantically verified

**Applies to:** risk registers, dependency maps, requirement matrices, task cross-references, mitigation ownership.

**Finding:** A document can contain a syntactically valid `PL-xxxx` reference while still pointing to a task that has nothing to do with the stated risk, mitigation, or evidence. Presence-only checks can therefore pass misleading governance links.

**Required behavior:** prompts and audits that require related task IDs must validate each referenced ID against current root `TASKS.md` semantics, not merely regex/format presence. Incorrect but well-formed task links are a material governance defect.

**Origin:** `M00-C001 / PL-0010_CHATGPT_AUDIT_V01.md`.

### AL-PL-0010 — Publication evidence must respect the final-log boundary

**Applies to:** all Codex logs whose final content is committed and pushed in the same publication commit.

**Finding:** A log cannot truthfully include the SHA or post-push command output of the commit that contains its final content without a follow-up edit commit. Pre-publication `Everything up-to-date` output must not be labeled as publication evidence.

**Required behavior:** Codex logs record actual staged validation and clearly identify the publication boundary; ChatGPT independently verifies the final pushed head, remote equality, and clean status after publication.

**Origin:** `M07-C001-R01 / CHATGPT_AUDIT_V03.md`.

### AL-PL-0011 - Camera-prior provenance and ambiguity must fail closed

**Applies to:** reconstruction camera-prior ingestion, PackScan metadata
candidate discovery, and reusable backend input contracts.

**Finding:** A prior model can expose provenance fields as optional while a
generic assessment boundary accepts an otherwise-valid prior when source
digest/revision binding is absent. Duplicate metadata handling that toggles a
candidate out on the second duplicate can also reintroduce one on a third,
silently selecting an ambiguous payload.

**Required behavior:** require exact source-package, working-set, and image
identity binding before backend use; track ambiguous candidate keys
separately so any duplicate count rejects the key and never selects a
candidate. Add production-boundary tests for missing binding and two-or-more
duplicate candidates, including odd duplicate counts.

**Origin:** `M07-C001 / PL-0167_CHATGPT_AUDIT_V01.md`.

### AL-PL-0012 - Feature-extraction configuration must stay backend-neutral

**Applies to:** M07 feature-extraction configuration and later reconstruction stages.

**Finding:** A named preset can silently become an engine-specific execution path, an untraceable bag of CLI flags, or an unsupported claim of packaging-performance optimization.

**Required behavior:** keep the preset immutable and PackLab-owned; validate bounds and unsupported options; serialize it canonically with a provenance digest; map engine parameters only at the adapter boundary; label the first consumer-packaging preset as an explicit initial configuration rather than physical benchmark evidence; and do not execute or install the external engine in the configuration task.

**Origin:** `M07-C001 / PL-0167_CHATGPT_AUDIT_V02.md` and PL-0168 frontier authorization.

## Audit history pointers

- `M00-C001` — milestone batch V01: PL-0006..PL-0009 and PL-0011..PL-0018 **AUDITED_PASS**; PL-0010 **CHANGES_REQUIRED** because the risk register's Related PL task IDs included multiple semantically unrelated task links. M00 remains open pending PL-0010 remediation and final milestone re-audit.
- `PL-0001-C001 / CHATGPT_AUDIT_V01.md` — **AUDITED_PASS**. Repository structure/ownership specification accepted. Local first-bootstrap commands remain Codex E1/E2 evidence; actual GitHub scope, document content, commit ancestry, push state, and protected-file isolation were independently inspected.
- `PL-0002-C001 / CHATGPT_AUDIT_V01.md` — **AUDITED_PASS**. PackLab glossary accepted against all 88 frozen criteria. Actual GitHub range contained only `GLOSSARY.md` plus the matching Codex log. Local Git/PowerShell commands remain Codex E1/E2; glossary semantics and final diff were independently inspected.
- `PL-0003-C001 / CHATGPT_AUDIT_V01.md` — **AUDITED_PASS**. ADR process and ADR-0001 accepted against all 123 frozen criteria. Actual GitHub range contained only the two authorized ADR documents plus the matching Codex log. A reusable log-metadata rule was added to avoid self-referential future commit SHAs.
- `PL-0004-C001 / CHATGPT_AUDIT_V01.md` — **AUDITED_PASS**. Supported host/device baseline accepted against all 128 frozen criteria. Current Acer host facts remain local E1/E2 evidence; GitHub scope/privacy/architecture and contemporary Apple device/ARKit facts were independently checked. Integrated-GPU AdapterRAM handling was retained as a reusable diagnostic caution.
