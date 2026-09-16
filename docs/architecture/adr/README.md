# PackLab Architecture Decision Records

## Purpose

An Architecture Decision Record (ADR) captures a durable PackLab architecture choice, the reasoning behind it, the alternatives considered, and the constraints that future work must preserve. ADRs make decisions reviewable and keep architectural history recoverable; they are not implementation plans, task status, or a second project tracker.

An ADR is required when a durable architectural choice changes or freezes one or more of the following:

- repository or module boundaries;
- cross-platform contracts or ownership;
- a major framework, runtime, or tool selection;
- responsibility boundaries for an external engine;
- persistence or storage architecture;
- geometry/CAD source-of-truth rules;
- security or trust boundaries;
- CI, build, or distribution architecture; or
- an already accepted architectural decision.

An ADR is not automatically required for routine implementation detail, typo fixes, link/format corrections that do not change a decision, ordinary refactors that preserve existing contracts, or task-status changes. A change that appears routine but alters a listed boundary must be treated as an architectural change and assessed for an ADR.

## Identity and file naming

ADRs use a permanent sequential number and a descriptive lowercase-kebab-case slug:

~~~text
ADR-0001-<lowercase-kebab-slug>.md
ADR-0002-<lowercase-kebab-slug>.md
...
~~~

Numbers are assigned once and are never reused. Rejection, deprecation, or supersession does not release an ADR number. The sequence is repository-wide, and a new ADR must use the next available number after checking this index and repository history. The slug describes the decision and should remain stable after publication unless a traceable, non-semantic correction is needed.

## Lifecycle and statuses

Every ADR has one of these statuses:

| Status | Meaning |
| --- | --- |
| Proposed | The decision is drafted for review; it is not yet an accepted PackLab architecture constraint. |
| Accepted | The decision is approved through the PackLab audited task/session process and any explicitly required owner decision. It is an active architecture constraint until superseded or deprecated. |
| Rejected | The proposal was reviewed and intentionally not adopted. Its history remains available so the decision is not reconsidered without context. |
| Deprecated | The decision is no longer recommended or active, but no replacement has necessarily been accepted. The record remains immutable history except for traceable non-semantic corrections. |
| Superseded | A later accepted ADR replaces this decision. The old record remains preserved and links to the replacement. |

Codex may draft an ADR only when the active prompt explicitly authorizes that work. Codex does not self-accept architecture decisions. Acceptance must come through the PackLab audited task/session process and, where the prompt or decision requires it, an explicit owner decision. A builder log is implementation evidence, not acceptance.

Accepted ADR history is preserved. A material change to an accepted ADR normally requires a new ADR whose relationship records that it supersedes the earlier decision; the earlier file is not silently rewritten to hide the original decision. A typo, link, or formatting correction that does not change the decision may be made in place only with traceable review in the applicable audited workflow. If the correction changes meaning, use a new ADR.

## Required ADR structure

Each ADR must contain the following sections and metadata. A later ADR may add focused sections, but it must not omit these fields or invent a competing lifecycle format.

~~~markdown
# ADR-NNNN — Title

- Status: Proposed | Accepted | Rejected | Deprecated | Superseded
- Date: YYYY-MM-DD
- Decision scope: What systems, boundaries, or contracts this decision covers.
- Supersedes: ADR-NNNN or None
- Superseded by: ADR-NNNN or None

## Context / problem
Why a durable decision is needed and what constraints apply.

## Decision
The adopted architecture and explicit boundaries.

## Rationale
The PackLab-specific reasons for selecting it.

## Alternatives considered
The credible alternatives and why they were or were not selected.

## Consequences / trade-offs
Positive and negative effects, operational costs, and follow-on work.

## Constraints / invariants
Rules that implementation and later decisions must preserve.

## References / evidence
Source contracts, prior ADRs, prompts, audits, benchmarks, or owner decisions.
~~~

The Date records the decision record’s publication/review date, not an invented implementation completion date. References must be precise enough for an auditor or later decision author to reproduce the relevant context.

## Authority and relationships

- Root TASKS.md remains the only live H!veAI/project-status tracker. ADRs record architecture decisions, not current task, progress, actor, or workflow state.
- REPOSITORY_STRUCTURE.md remains the PackLab ownership and dependency specification. ADRs may clarify or intentionally change it only through the audited process.
- GLOSSARY.md remains the PackLab terminology contract. ADRs may reference its definitions but must not silently redefine terminology.
- An ADR cannot silently override a higher-authority active task or session scope. The active prompt controls what a particular implementation pass is authorized to change.
- When a new accepted ADR intentionally changes a canonical architecture contract, the same audited change or a specifically authorized follow-up task must reconcile every affected canonical document. Until reconciliation is complete, the existing contract remains the operational reference.
- Session prompts, implementation logs, audits, and criteria provide decision evidence and review history; they are not themselves ADRs and do not replace an accepted decision record.

## ADR index

This table is an architecture-record index, not a live task ledger. Supersession is recorded explicitly so decision history remains navigable.

| ADR ID | Title | Status | Supersedes / Superseded by |
| --- | --- | --- | --- |
| ADR-0001 | Use one PackLab monorepo with explicit platform, domain, schema, architecture-documentation, and coordination boundaries | Accepted | Supersedes: None; Superseded by: None |

New rows must preserve permanent IDs, exact current status, and any supersession relation. Do not add current-task or project-progress columns to this index.
