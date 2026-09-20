# PackLab Architecture-Change Protocol

## Architecture change versus bounded implementation

An architecture change alters a canonical ownership boundary, contract
meaning, system topology, authority, or compatibility philosophy. A bounded
implementation detail stays inside an already approved boundary and preserves
its public ownership, units, semantics, and authority. Size or code volume
alone does not decide the classification.

When uncertain, the builder treats the contradiction as architectural and
stops with `ADR_REQUIRED` rather than choosing a new boundary silently.

## ADR-required boundaries

An approved ADR is required before implementation changes any of these
canonical boundaries:

- monorepo topology or ownership of major areas;
- PackScan authority, schema philosophy, compatibility, or immutable-evidence
  meaning;
- separation of Scan Mesh, Scan Master, and editable Design Model;
- canonical engineering units or coordinate-system truth;
- major engine ownership, such as reconstruction, CAD/BREP, rendering, or
  capture authority; or
- live tracking/project-status authority.

The existing ADR process in `docs/architecture/adr/README.md` and
`docs/architecture/adr/ADR-0001-monorepo-architecture.md` is the reference
for decision records, status, alternatives, consequences, and linkage.

## Builder stop behavior

If a frozen prompt conflicts with an established boundary or implementation
would require an unapproved architecture decision, the builder stops before
the conflicting change, records `ADR_REQUIRED`, the evidence and exact
decision needed, and hands off to ChatGPT/owner governance. The builder does
not implement a workaround, rewrite `TASKS.md`, or claim partial architecture
acceptance.

Codex must not create an opportunistic ADR merely to keep moving when the
prompt requires stopping for ChatGPT or an owner decision. The builder may
reference the existing process and record the need; only a later authorized
prompt may define the ADR task and implementation scope.

## Decision and implementation linkage

After evidence review, ChatGPT may issue a dedicated ADR work order when the
change is genuinely architectural, the affected boundary and alternatives
are clear, the owner decision is available where needed, and the task remains
within governed scope. A later implementation prompt must link the approved
ADR by repository path/ID and commit or GitHub URL, state which decision it
implements, and preserve all unaffected boundaries. An ADR approval is not
itself implementation evidence.

## Milestone-batch behavior

In an explicitly authorized milestone batch, an architecture contradiction or
`ADR_REQUIRED` stop ends execution at that child before later children start.
Earlier child evidence is preserved; the master log records the exact
contradiction, last completed child, and `BATCH_STOPPED` handoff. A batch
exception permits sequential frozen children but never bypasses ADR review.

## Authority and scope boundary

GitHub `main` is repository truth and root `TASKS.md` is the sole live
project-status tracker. This document is evidence/reference only and does not
create tracker state, an ADR, an architecture change, or M01 work. This task
creates no implementation change to topology, PackScan, scan/design
separation, units, coordinates, engine ownership, or tracking authority.
