# PL-0352 Codex Log V01 — Private Installer Artifact Retention

Date: 2026-10-15
Repository: `Sekiph82/PackLab` (**private**)
Task: PL-0352 only
Result: **READY_FOR_INDEPENDENT_AUDIT**

## Authorization and synchronization

- Read the complete `PL-0352_CODEX_MASTER_PROMPT_V02.md`, matching `PL-0352_CHATGPT_AUDIT_CRITERIA_V02.md`, root `TASKS.md` for the live task authorization, PL-0351 independent PASS, PL-0350 independent Installer PASS, and the owner internal factory deployment decision.
- Started in an isolated Codex worktree at the current `origin/main` commit `0f0e740372b4e45cad0cc63b8214c23cda9bc4ce`. The owner Desktop checkout and its existing modified/untracked files were left untouched.
- Published PL-0352 implementation to private `main`; final implementation commit before this log: `484b512f01d18c69f303f096c9f6a23327e3e9ce`. No root `TASKS.md`, ChatGPT audit, PL-0350/PL-0351 acceptance report, app source, build lock, or license-rights file was modified.

## Retained artifact evidence

The live repository setting was read through GitHub's Actions retention API: `days=90`, `maximum_allowed_days=400`. The private source artifact was still available, unexpired, and due to expire at `2026-10-15T23:08:28Z`.

The single retained candidate is:

| Field | Verified value |
| --- | --- |
| Private repository | `private=true`, `visibility=private` |
| Original source run / artifact | `38649528145` / `11935390977` |
| Original source revision | `452fe8934b0d56011af8c117555dd059d5c63462` |
| Original source ZIP | `877253435` bytes; SHA-256 `3e9762e4d3faf6d0363f9714bfbdcb0d0b2d9dc9e73769ebfaac757c9af23e15` |
| Installer EXE | `877598790` bytes; SHA-256 `3e7c13c18674fbe0a4de843a2ac329055850d07901a7e33fac8a3dc742d92da6` |
| Retention transfer run / artifact | `38707054365` / `11959245441` |
| Retention run source revision | `602dfed427d1f82eea17e7ce2e2faac750189570` |
| Retained artifact name | `packlab-internal-installer-candidate-pl0350-warm-452fe8934b0d56011af8c117555dd059d5c63462` |
| Retained ZIP | `877601969` bytes; SHA-256 `b976c7d4e48985329c8f51a68b250ff6e565930ed993b0409b9c5d561c3da4ac` |
| Actual expiry | `2026-12-14T08:38:33Z` (60 days) |
| Authenticated private readback | Run `38707367887`, successful, workflow revision `0f58dff1f6f62b006cbf79fb207860010af51700` |

Hosted readback `38707367887` downloaded the retained artifact through its authenticated private GitHub URL. It verified the returned archive byte length and outer digest against artifact API metadata, opened the ZIP, checked the source/retention origin manifest and notices/provenance references, and recomputed the embedded Installer size and SHA-256. Final log line: `retained_artifact_id=11959245441 ... installer_bytes=877598790 installer_sha256=3e7c13c18674fbe0a4de843a2ac329055850d07901a7e33fac8a3dc742d92da6 private_read=PASS`.

The outer ZIP digest changed as expected after repacking. The Installer EXE bytes did not change. The retained bundle contains the exact Installer, its installer metadata, original installed-smoke evidence, and a SHA-bound `retention-origin.json`. Its source lineage records the original run/artifact/ZIP, source commit, EXE hash, notice/compliance report paths and digests, private scope, `legal_review_required=true`, and `public_release_authorized=false`.

## Implementation and policy

- Added a manual, serialized, `main`-only Linux retention bridge. It has only `actions: read` and `contents: read`, pins its checkout/upload actions by full SHA, rejects a public repository, wrong/expired/source-mismatched artifact, changed archive or EXE hashes, missing evidence, duplicates, and a projected 5,000,000,000-byte active-artifact cap. A later retry detects the already retained exact artifact and skips upload; it cannot create another copy.
- The bridge transfers only the exact known Installer and small metadata/evidence files. It downloads and verifies the original source archive in the hosted runner; no new Installer, OCCT, or OCP build ran. The token is not forwarded to the signed blob host after GitHub’s authenticated redirect.
- Added `docs/packaging/GITHUB_ACTIONS_ARTIFACT_RETENTION_POLICY.md` with bounded A–E classes, purpose/count/size/retention, source of truth, expiry monitoring, private access, recovery, owner-authorized deletion, and the separate legal/factory rollout boundary.
- Regular Installer uploads remain one-day transient artifacts. Only the one accepted private candidate uses 60 days. SDK/OCP runtime artifacts remain short-lived; recovery/quarantine is bounded to at most 14 days. Diagnostics were shortened from 14 to 3 days, and the disposable preview installer from 14 to 1 day. The preview upload action is now full-SHA pinned. No macOS artifact-upload path was present to change.
- Migrated the PL-0351 smoke workflow to retained artifact `11959245441` only after it was created and read back successfully. It now checks the new archive identity, private repository, transfer run/steps, the successful private readback run, and `retention-origin.json`, while keeping the original PL-0350 source run/artifact, ZIP digest, source revision and exact EXE digest in the chain. No PL-0351 install smoke was rerun in this retention task.

## Storage and cost

- Before retention: 182 active Actions artifacts totaling `3,995,503,724` bytes; cache usage separately was `964,386,418` bytes across 16 cache entries.
- After retention: 183 active Actions artifacts totaling `4,873,105,693` bytes (`4.873 GB` decimal), including exactly one new retained artifact of `877,601,969` bytes. The bridge rejects an upload if projected active artifact storage would exceed 5,000,000,000 bytes.
- GitHub's account billing endpoint was unavailable to the current token and requires an extra `user` scope, which was not requested. Account plan allowance and actual accrued charge therefore remain unverified. GitHub's published shared artifact/Packages storage rate is `$0.25 USD/GB-month`; the exact payload for 60 days is approximately `$0.41 gross` before plan allowance and billing-cycle rounding. No precise invoice amount is claimed.
- GitHub Actions cache remains distinct from workflow artifact retention; no cache was expanded, removed, or treated as a durable installer store.

## Validation and failed-attempt recovery

Focused local verification:

- `uv run --locked python -m pytest tests/ci/test_pl0351_clean_windows_workflow.py tests/ci/test_pl0352_artifact_retention.py -q` — **13 passed**.
- `uv run --locked python -m ruff check tools/packaging/pl0352_artifact_retention.py tests/ci/test_pl0351_clean_windows_workflow.py tests/ci/test_pl0352_artifact_retention.py` — **passed**.
- `uv run --locked python -m ruff format --check tools/packaging/pl0352_artifact_retention.py tests/ci/test_pl0351_clean_windows_workflow.py tests/ci/test_pl0352_artifact_retention.py` — **passed**.
- PyYAML parsed the bridge, migrated smoke workflow, main Windows build workflow, and preview workflow; both embedded bridge Python scripts compiled — **passed**.
- `git diff --check` and staged `git diff --cached --check` — **passed**.
- Negative checks cover expired/wrong-hash/wrong-producer/wrong-artifact/public/wrong-ref inputs, wrong EXE identity, missing notice evidence, storage cap, duplicate candidate, and unapproved reupload.

Hosted attempts and recovery:

1. `38706662893` stopped before transfer: initial YAML had malformed heredoc scalar syntax; corrected and YAML parsing was added locally.
2. `38706797156` stopped before transfer: the workflow token could not read repository administrator retention settings (403); removed that unsupported token request. The preflight setting was independently read with the available authenticated GitHub CLI, and the actual created expiry is checked after upload.
3. `38706912066` stopped before transfer: Python forwarded an incompatible Authorization header through GitHub's ZIP redirect (401); changed the bridge to follow the redirect manually without sending the GitHub token to the blob host.
4. `38707054365` passed source ZIP and EXE verification and uploaded the single artifact. Its final readback step hit a verifier `NameError` after the archive upload; the artifact remained in private storage. The fixed workflow now detects that exact artifact and skips any duplicate upload.
5. `38707367887` completed successfully in verification-only mode: authenticated private read, outer archive digest and size, origin manifest, and exact embedded Installer digest and size all passed.

No local copy of the ~0.88 GB Installer was downloaded. No owner Desktop files, working PackLab.exe, OwnerDev, or SDK/OCP checkpoints were edited, overwritten, or deleted. No release, tag, signing operation, or public repository change was made. Formal legal review and factory rollout authorization remain required/not granted; this log does not declare legal clearance.

## GitHub evidence

- Retention bridge implementation and policy: private `main`, commits `d46cfb0a30f65716149544a023e0f500d578a38b`, `8c6e8e682e6caf28265500286e8f914adff72082`, `b3e16e6d0a2ead2ec845a68a801c9cd7e4f3fdc9`, `602dfed427d1f82eea17e7ce2e2faac750189570`, and `0f58dff1f6f62b006cbf79fb207860010af51700`.
- Retained artifact producer: https://github.com/Sekiph82/PackLab/actions/runs/38707054365
- Successful private readback: https://github.com/Sekiph82/PackLab/actions/runs/38707367887
- Original warm Installer producer: https://github.com/Sekiph82/PackLab/actions/runs/38649528145
- Implementation and migration commit: `484b512f01d18c69f303f096c9f6a23327e3e9ce`.
- Repository visibility rechecked as `private=true`, `visibility=private`; root `TASKS.md` unchanged.

**Handoff: AWAITING_AUDIT.** `READY_FOR_INDEPENDENT_AUDIT` — actual private retained Installer provenance checkpoint and future scoped retention controls are in place and verified. This status is not legal approval or factory deployment acceptance.
