# M15-C001 - Kenya Packaging Library Master Codex Prompt V01

Milestone: **M15 - Kenya Packaging Library**
Ordered children: **PL-0332 through PL-0346**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

Master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/MASTER_CODEX_LOG_V01.md

## Start rule

1. Synchronize the execution checkout non-destructively with latest `origin/main`.
2. Preserve owner-local work and unrelated checkouts.
3. Verify live root `TASKS.md` authorizes M15-C001 / PL-0332→PL-0346 and actor CODEX.
4. Read:
   - M14 final audit;
   - M13 final audit;
   - M09 physical-validation deferral;
   - ADR-0005;
   - this master prompt/criteria;
   - exact child prompt/criteria before each child.
5. Confirm M16+ is unauthorized.
6. Root `TASKS.md` is ChatGPT-owned. Do not edit it.

## Frozen M15 architecture

- Packaging Library is a Studio-level local-first library accessible through existing `Route.LIBRARY`; browsing must not require an open project.
- Canonical library identity/state is path-free and machine-independent. Runtime library/project roots are injected separately.
- Existing PackLab projects and M14 artifacts remain source authority. Library records link exact project/revision/digest IDs and never mutate source geometry/artwork/material/render artifacts.
- Supplier facts, user declarations and PackLab estimates remain provenance-distinct. Estimates never become supplier facts or certification.
- Supplier attachments are opaque local bytes in content-addressed library storage, never executed/fetched remotely and never committed as evidence to Git.
- UI uses accepted library/domain/store services; widgets do not become canonical authority.
- 3D preview reuses existing PackLab `QtRasterViewportAdapter`/SceneModel path.
- Backup/restore and contact-sheet export are offline and privacy-safe.
- Existing M09 physical validation and all non-manufacturing/non-certification limits remain in force.
- No new runtime network/download/cloud dependency or unreviewed dependency.
- M16+ is unauthorized.

## Exact execution order

PL-0332 → PL-0333 → PL-0334 → PL-0335 → PL-0336 → PL-0337 → PL-0338 → PL-0339 → PL-0340 → PL-0341 → PL-0342 → PL-0343 → PL-0344 → PL-0345 → PL-0346.

For each child:

1. read exact child prompt + criteria;
2. implement only that child and accepted predecessor seams;
3. run focused/predecessor tests;
4. run locked full repository suite;
5. run changed-file Ruff/format and targeted mypy/compile where applicable;
6. run dependency/lockfile, privacy/security/scope checks;
7. confirm root `TASKS.md` unchanged and M16+ not started;
8. publish implementation/evidence commit(s);
9. publish distinct child-log-only commit ending exactly `READY_FOR_INDEPENDENT_AUDIT`;
10. verify local/origin/GitHub publication parity;
11. update `coordination/sessions/M15-C001/MASTER_CODEX_LOG_V01.md`;
12. continue automatically while all mandatory gates are green.

Do not wait for intermediate ChatGPT audits.

## Mandatory stop conditions

Stop immediately and hand off if any child requires:

- authority ambiguity or provenance promotion;
- supplier fact inferred from PackLab estimate;
- geometry/artwork/material source mutation to make Library metadata work;
- ambient absolute path in canonical identity;
- unsafe/unbounded attachment handling;
- runtime network/cloud/download;
- unreviewed dependency;
- archive/path traversal or restore-overwrite ambiguity;
- UI bypass of canonical service/state authority;
- locked-suite failure not proven unrelated;
- dependency/license/privacy/security issue;
- owner decision;
- M16+ work.

On stop:

- preserve valid completed children;
- publish exact blocker log/evidence;
- set master status `BATCH_STOPPED`;
- record accepted/pending frontier;
- confirm M16 not started;
- end master log exactly `AWAITING_MILESTONE_AUDIT`;
- stop.

## Successful handoff

If all 15 children are builder-green:

- master index contains PL-0332→PL-0346 in exact order;
- every child has implementation/evidence + distinct log-only publication;
- every child log ends `READY_FOR_INDEPENDENT_AUDIT`;
- locked full suite and static/scope/dependency checks are current;
- final local/origin/GitHub main parity is clean;
- no root TASKS edit by Codex;
- M16 started: NO;
- set `BATCH_COMPLETED`;
- end master log exactly `AWAITING_MILESTONE_AUDIT`;
- stop for independent ChatGPT milestone audit.
