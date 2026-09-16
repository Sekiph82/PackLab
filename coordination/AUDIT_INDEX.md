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

## Audit history pointers

- `PL-0001-C001 / CHATGPT_AUDIT_V01.md` — **AUDITED_PASS**. Repository structure/ownership specification accepted. Local first-bootstrap commands remain Codex E1/E2 evidence; actual GitHub scope, document content, commit ancestry, push state, and protected-file isolation were independently inspected.
