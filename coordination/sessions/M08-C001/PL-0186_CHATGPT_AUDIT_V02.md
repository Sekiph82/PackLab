# PL-0186 — ChatGPT Independent Audit V02

Date: 2026-10-01  
Task: **PL-0186 V03 — SAM 2.1 runtime/config provenance remediation**  
Audited implementation: `ca2bfc39254135d56f59011d07f1f06b49b251cf`  
Audited log head: `43b1a95979aa9916a7d6022880bd5b6863477799`  
Decision: **AUDITED_PASS**

## Scope reviewed

- Source audit:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_V01.md
- V03 prompt:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CODEX_PROMPT_V03.md
- V03 criteria:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_CRITERIA_V03.md
- V03 Codex log:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CODEX_LOG_V03.md
- Implementation:
  https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/sam21_backend.py
- Tests:
  https://github.com/Sekiph82/PackLab/blob/main/tests/core/test_sam21_backend.py
- Owner decision:
  https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0004-sam2.1-segmentation-backend.md

## Independent findings

### 1. Expected and observed SAM 2 identities are now separated — PASS

`SAM21RuntimeIdentity` records approved identity separately from observed local facts.

The approved repository/revision remain fixed project policy, while the observed fields record:

- availability;
- package/version signal;
- source form;
- module path for diagnostics;
- actual source revision;
- identity match result;
- verification reason.

When SAM 2 is unavailable, the observed revision is `None`, source form is `unavailable`, and the approved frozen revision is no longer presented as an observed fact.

A source installation becomes executable only when the imported `sam2` module resolves into a Git checkout whose:

- origin matches the approved `facebookresearch/sam2` repository;
- actual HEAD equals `2b90b9f5ceec907a1c18123530e92e794ad901a4`;
- `sam2/` subtree is clean;
- approved Hydra config exists and passes its pinned digest.

Mismatched or unverifiable source identity fails closed.

### 2. Executed Hydra config and verified config are now the same authority — PASS

The misleading external `config_path` authority was removed from the production backend/runtime constructors.

The runtime derives the exact config from the verified imported SAM 2 checkout:

`sam2/configs/sam2.1/sam2.1_hiera_b+.yaml`

Predictor construction uses the corresponding Hydra ID:

`configs/sam2.1/sam2.1_hiera_b+.yaml`

and execution is allowed only after the verified checkout's config passes the pinned SHA-256.

I independently fetched this exact file at the approved upstream revision and computed:

`37d6c56b07a7f8d08baaa314315c60dc3aabe2edc66cd92bac6d1ed50038e788`

This exactly matches `SAM21_CONFIG_SHA256` in PackLab.

Upstream `build_sam2()` at the approved revision uses Hydra `compose(config_name=config_file, ...)`, so this binding closes the V02 finding: PackLab now verifies the same packaged config authority that the runtime resolves.

Upstream source:
https://github.com/facebookresearch/sam2/blob/2b90b9f5ceec907a1c18123530e92e794ad901a4/sam2/build_sam.py

### 3. Checkpoint provenance remains accepted — PASS

The V02 accepted checkpoint gate is preserved:

- checkpoint: `sam2.1_hiera_base_plus.pt`
- exact size: `323606802` bytes
- SHA-256: `a2345aede8715ab1d5d31b4a509fb160c5a4af1970f199d9054ccfb746c004c5`
- no checkpoint binary in Git;
- no application-time auto-download;
- wrong filename/size/hash fails closed.

### 4. Runtime and network authority remain bounded — PASS

The production path remains local-only. No hosted inference, credentials, hidden remote service or runtime download fallback was introduced.

The live builder environment is truthfully reported as native Windows with PyTorch, torchvision and SAM 2 unavailable. No native model-execution claim is manufactured.

### 5. Existing segmentation behavior and task boundary remain intact — PASS

Point/box prompts, source-grid coordinates, confidence/malformed-output rejection, checkpoint gate, raw-model-output provenance and source-byte immutability remain preserved.

No PL-0187 PackLab post-processing behavior was added.

## Independent source/diff review

The V03 implementation commit changes only:

- `core/src/packlab_core/sam21_backend.py`
- `tests/core/test_sam21_backend.py`

The following protected areas were not changed by the implementation:

- `TASKS.md`;
- owner ADR;
- ChatGPT audit/criteria artifacts;
- lockfiles;
- model/checkpoint binaries;
- PL-0187+;
- M09;
- private scan/signing material.

The V03 log is a separate log-only commit and ends exactly with:

`READY_FOR_INDEPENDENT_AUDIT`

## Test and evidence disposition

Builder evidence records:

- focused/regression suite: `33 passed`;
- full locked suite: `843 passed, 6 skipped, 1 deselected`;
- changed-file Ruff/format/mypy/compileall/diff checks passed;
- repository-wide unrelated static debt remains isolated to unchanged files.

Independent source inspection confirms the new tests cover:

- unavailable SAM 2 without fabricated revision;
- verified approved source checkout;
- mismatched commit;
- unverifiable source;
- config digest mismatch;
- external lookalike config rejection;
- portable provenance;
- checkpoint regressions;
- point/box regressions;
- malformed output;
- source immutability;
- no-network boundary.

## V03 criteria matrix

| # | Result | Finding |
|---:|---|---|
| 1 | PASS | Live tracker authorized PL-0186 V03 / CHANGES_REQUIRED / CODEX before implementation. |
| 2 | PASS | Accepted V02 boundaries are preserved. |
| 3 | PASS | Expected and observed runtime identity are separate. |
| 4 | PASS | Approved revision is not emitted as observed unless verified. |
| 5 | PASS | SAM 2 unavailable reports no observed source revision. |
| 6 | PASS | Mismatched/unverifiable installed source fails closed. |
| 7 | PASS | Observed source form/path/revision/version signal are captured; approved Git source form is verified. |
| 8 | PASS | Config verification is bound to the config actually resolved by the approved SAM 2 package. |
| 9 | PASS | Executed config ID and SHA-256 are recorded in runtime/provenance. |
| 10 | PASS | External lookalike config cannot authorize runtime. |
| 11 | PASS | Misleading external config authority was removed. |
| 12 | PASS | Approved checkpoint size/SHA remain unchanged. |
| 13 | PASS | Required V03 regression and negative cases are present. |
| 14 | PASS | No later-task/dependency/hosted/private/binary/protected scope expansion. |
| 15 | PASS | Required validation is recorded; changed files pass targeted static checks. |
| 16 | PASS | Codex did not edit lifecycle/owner/audit authority files. |
| 17 | PASS | Implementation and V03 log are separate commits. |
| 18 | PASS | V03 log is complete and ends with the required handoff marker. |

## Verdict

`AUDITED_PASS`

PL-0186 is independently accepted.

PL-0187 may now be authorized. PL-0188+, later M08 work and M09 remain unauthorized until their ordered frontiers are independently opened.
