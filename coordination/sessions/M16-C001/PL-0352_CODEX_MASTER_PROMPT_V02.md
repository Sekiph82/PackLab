# PL-0352 | ONE-SHOT CODEX MASTER PROMPT V02 | PRIVATE Artifact Retention & Installer Preservation

**Execute ONLY PL-0352.** Repo `Sekiph82/PackLab` is **PRIVATE**. Owner's product is proprietary INTERNAL factory software, not a public GitHub product. Supersede obsolete task wording "public repository". Do NOT make repo public, publish a GitHub Release or Installer, license/open-source PackLab proprietary work, sign artifacts, or declare legal clearance.

Read ONCE:
- Root `TASKS.md` (ChatGPT-owned, currently PL0352 next).
- PL0351 independent PASS: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CHATGPT_AUDIT_V01.md
- PL0350 independent Installer PASS: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_ALL_REMAINING_WORK_ONE_SHOT_CHATGPT_AUDIT_V02.md
- Owner multi-PC Kenya internal policy: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OWNER_INTERNAL_FACTORY_DEPLOYMENT_DECISION.md
- ChatGPT audit criteria V02: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0352_CHATGPT_AUDIT_CRITERIA_V02.md
- Relevant upload/download-artifact paths in `.github/workflows/windows-studio-build.yml`, `.github/workflows/pl0351-clean-windows-installer-smoke.yml` and existing Windows/macOS policy, not new M17 implementation.

## P0 — Owner binary at imminent expiry

PL0350 **known authentic WARM Installer** (source `452fe8934b0d56011af8c117555dd059d5c63462`):
- Private GitHub Actions producer run `38649528145`; artifact ID `11935390977`; upload archive **877,253,435 bytes**, SHA256 `3e9762e4d3faf6d0363f9714bfbdcb0d0b2d9dc9e73769ebfaac757c9af23e15`, **expires 2026-10-15 23:08:28 UTC**.
- Installed Windows Installer EXE inside that archive: **877,598,790 bytes**, SHA256 `3e7c13c18674fbe0a4de843a2ac329055850d07901a7e33fac8a3dc742d92da6`.
- Independent PL0351 hosted fresh-runner run `38703546854` PASSED installed smoke; no rebuild.
- Existing verified owner-retained warm Installer reported in Codex artifact storage. **PRESERVE.** Do NOT download new 0.88GB copies to owner's C:, overwrite Desktop PackLab, OwnerDev, working EXE, or wipe OCCT/OCP checkpoints.

**Act first:** query live GitHub artifact expiry/validity, private Actions retention maximum and actual storage/budget settings. If before expiry AND artifact/usage permit one no-native controlled retention transfer, use **one** manual, SHA-pinned, private Windows/Linux runner to retrieve original ID, verify original archive SHA/bytes + exact internal EXE SHA/bytes and source, and reupload **one** bounded private retained Installer+metadata evidence bundle at the maximum **allowed/reasonable** retention for a Kenya commissioning horizon (~2 months). Verify the newly created artifact's ID, byte length, **new** archive digest, expiry and private read. Never pretend outer zip digest remains unchanged after repacking. NO OCCT/OCP/Installer recompile; no GitHub Release. Keep transfer <= one 0.9GB instance and log actual quota/cost. If retention max < horizon, explicitly document remaining gap and suggest one authorized persistent owner-private vault, **without uploading to external storage automatically**.

If original artifact already expired/inaccessible, no circumventing expiry or falsified cache HIT. Prefer the existing owner-authenticated local warm EXE and ask for an **explicit authorized secure upload destination/action** if a remote durable copy is still needed. Do NOT recompile simply to refresh retention. Never bypass GitHub tool/policy denials.

## P1 — Forward-looking artifact policy

Implement a clear `PL0352` category registry / small docs and testable GitHub workflow retention controls for:
(A) accepted installer **private owner internal deployment candidate**,
(B) exact corresponding source/NOTICE/legal evidence,
(C) verified OCCT SDK / OCP runtime and provenance manifests,
(D) lightweight smoke/diagnostic artifacts,
(E) short disposable staging/temporary evidence.

Respect GitHub repo max retention days/storage quotas and distinguish GitHub **cache** from durable binary retention. Minimize long-lived gigabyte clones: only approved single accepted candidates retained long; ephemeral native caches may keep short retention but source/metadata must be persistent and SHA-verifiable. Do NOT casually convert every job's 1-day native artifact to 90 days and exhaust storage.

Inventory actual Actions artifact types, sizes, current `retention-days`, private GitHub repo limits, and existing policy. Set bounded explicit classes in minimal existing workflow changes, guard required artifacts `if-no-files-found: error`, enforce least-privilege permissions and no customer/media/certs. Do not modify unrelated macOS CI except to record an applicable future policy; do not trigger a new native build.

Document expiry monitoring/manual refresh, deletion policy requiring owner authorization, legal/factory rollout boundary, private access controls and recovery procedure using exact SHA+run origin. For the installed test workflow, do not silently replace old exact artifact ID with another: migrate only if new retained artifact verified, with matching source+EXE hash and explicit origin chain. Add narrow negative tests for expired artifact, wrong hash, wrong scope, public leak, storage cap, missing notice, duplicate artifact and unapproved reupload.

## P2 — Verification and publication

Non-destructively sync current managed Codex worktree with `origin/main`. Root `TASKS.md` and ChatGPT audit files belong ONLY to ChatGPT. Do not change PL0350/PL0351 acceptance, app source, build locks, or package's licensing rights.

Run focused workflow/policy tests, YAML parse, Ruff/format/mypy as relevant and `git diff --check`. No local heavy test trees and **no 6-hour native jobs**. At most ONE tiny/bounded noncompiling hosted retention-bridge job if essential and authorized. Do not run generic disk cleanup. Owner C: lost free space even after prior scoped cleanup; preserve all private data and local original/retained application outputs.

Publish implementation and separate `coordination/sessions/M16-C001/PL-0352_CODEX_LOG_V01.md` to **private** `main`, with source, verification, transferred artifact IDs, actual new retention expiry, SHA evidence, cost/quota, permission scope, producer lineage and unchanged laptop. Finish with **READY_FOR_INDEPENDENT_AUDIT** only if real retention protection and needed policy proven; otherwise exact `BLOCKED_<reason>` and one narrowly described owner decision. No public release or factory deployment; `legal_review_required=true`.

**Finish this PL0352 end-to-end autonomously. Do not start PL0353/M17/PL0368 or require a new task prompt for routine code mistakes.**
