---
coordinationSchema: packlab-coordination/v1
artifactType: chatgpt-audit
cycleId: <CYCLE_ID>
version: <NN>
actor: CHATGPT
verdict: PENDING
promptPath: coordination/sessions/<CYCLE_ID>/CODEX_PROMPT_VNN.md
criteriaPath: coordination/sessions/<CYCLE_ID>/CHATGPT_AUDIT_CRITERIA_VNN.md
codexLogPath: coordination/sessions/<CYCLE_ID>/CODEX_LOG_VNN.md
auditedBase: <sha>
auditedHead: <sha>
---

# PackLab ChatGPT Audit VNN — <CYCLE_ID>

## Verdict

`AUDITED_PASS` / `CHANGES_REQUIRED` / `AUDITED_FAIL` / `BLOCKED` / `OWNER_REQUIRED`

## Scope audited

- Prompt:
- Criteria:
- Codex log:
- Base/head:
- Diff span:

## Evidence classification

### E1/E2 Codex evidence

- ...

### E3 independent ChatGPT evidence

- Files/diff inspected:
- Checks independently rerun/cross-checked:
- Checks not independently rerun and why:

### E4 owner evidence/decision

- ...

## Criteria matrix

| # | Result | Evidence / finding |
|---:|---|---|
| 1 | PASS/FAIL/UNVERIFIED/N/A | ... |

## Findings

### Critical

- ...

### High

- ...

### Medium

- ...

### Low

- ...

## Architecture / regression / security review

- Architecture boundaries:
- Regression risk:
- Test sensitivity / false-positive risk:
- Security/privacy:
- Scope leakage:

## Reusable audit learnings

- New `AL-PL-xxxx` entries to add to `coordination/AUDIT_INDEX.md`, or NONE.

## TASKS.md action

ChatGPT must update root `TASKS.md` after this audit:

- task row closure/open state;
- `## Project Status`;
- current actor;
- next action/frontier;
- blocker/correction state when applicable.

## Remediation

If verdict is not PASS, list the exact frozen correction set to carry into `CODEX_PROMPT_VNN+1.md` and matching criteria.

## Final conclusion

...
