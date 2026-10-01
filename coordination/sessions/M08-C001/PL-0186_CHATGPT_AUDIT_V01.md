# PL-0186 — ChatGPT Independent Audit V01

Date: 2026-10-01  
Task: **PL-0186 V02 — SAM 2.1 Hiera Base+ local PyTorch segmentation backend**  
Audited implementation: `ee3c15918271b78d758810dc7ac9080a553ae739`  
Audited log head: `1681dd8fd5a1c3fb8e32813f3f2b100ae2333504`  
Decision: **CHANGES_REQUIRED**

## Scope reviewed

- Owner decision:
  https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0004-sam2.1-segmentation-backend.md
- Prompt:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CODEX_PROMPT_V02.md
- Criteria:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_CRITERIA_V02.md
- Codex log:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CODEX_LOG_V02.md
- Backend:
  https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/sam21_backend.py
- Segmentation contract:
  https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/segmentation.py
- Tests:
  https://github.com/Sekiph82/PackLab/blob/main/tests/core/test_sam21_backend.py
- Dependency/license register:
  https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/DEPENDENCY_LICENSE_REGISTER.md

## Accepted findings

### Model and checkpoint identity — PASS

The implementation preserves the owner-approved frozen identity:

- repository: https://github.com/facebookresearch/sam2
- reviewed revision: `2b90b9f5ceec907a1c18123530e92e794ad901a4`
- model: SAM 2.1 Hiera Base+
- checkpoint: `sam2.1_hiera_base_plus.pt`
- config ID: `configs/sam2.1/sam2.1_hiera_b+.yaml`
- repository license: Apache-2.0.

The recorded checkpoint size and digest are independently corroborated by Meta's official Hugging Face model record:

- size: `323606802` bytes
- SHA-256: `a2345aede8715ab1d5d31b4a509fb160c5a4af1970f199d9054ccfb746c004c5`
- reference:
  https://huggingface.co/facebook/sam2.1-hiera-base-plus/blob/main/sam2.1_hiera_base_plus.pt

The checkpoint binary is not committed, and verification fails closed on wrong filename, size or digest.

### Network/runtime boundary — PASS

No hosted API, credentials, hidden remote inference or application-time model download path was introduced. Runtime imports are lazy and local. The actual builder environment truthfully reports PyTorch/torchvision/SAM 2 unavailable on native Windows, with no fabricated native execution claim.

### Backend isolation and mask behavior — PASS

SAM-specific code remains confined to `sam21_backend.py`. Downstream consumers continue to use PackLab segmentation contracts. Point/box prompt normalization, source-grid mask normalization, confidence validation, malformed output rejection, checkpoint failure behavior and RAW_CAPTURE immutability are covered through the public boundary.

### PL-0187 scope — PASS

No PackLab hole filling, edge cleanup or small-component-removal policy was added. Raw model output remains explicitly marked as unprocessed.

### Builder validation — ACCEPTED AS E2

The log records:

- focused/regression suites green;
- full locked suite: `839 passed, 6 skipped, 1 deselected`;
- targeted Ruff/mypy/format/compileall green;
- known unrelated repository-wide static debt isolated to unchanged files;
- no lockfile/model binary/private-data/later-task mutation.

These are builder evidence, not independent acceptance.

## Material findings

### Finding 1 — observed SAM 2 runtime revision is fabricated from the expected revision

`PyTorchSAM21Runtime.__init__` sets:

```python
self._sam2_revision = SAM21_UPSTREAM_REVISION
```

and `probe()` returns that value whether SAM 2 is unavailable or successfully imported.

Therefore the runtime report does **not measure the installed SAM 2 package/source identity**. An older, newer or locally modified SAM 2 installation would still be reported as the reviewed frozen revision `2b90b9f...`.

This violates the V02 criteria requiring exact runtime facts and provenance-bound execution. The current builder log is truthful because SAM 2 was unavailable, but the production capability boundary would manufacture a reviewed revision once a different local installation becomes importable.

Required correction:

- distinguish **expected/reviewed upstream revision** from **observed installed runtime identity**;
- when SAM 2 is unavailable, observed package/revision must be an explicit unavailable state;
- when available, record observable package/source identity, such as package version plus module path and, when the approved editable/git source form is used, the actual source commit;
- do not label an unverified local package as the reviewed commit;
- production availability must fail closed when the installed SAM 2 identity cannot be shown to match the owner-approved runtime form required by ADR-0004/V03.

### Finding 2 — the config file that is validated is not the config artifact that is executed

The backend receives `config_path`, and capability checks consider it valid when:

```python
self._config_path.name == Path(SAM21_CONFIG_ID).name
and self._config_path.is_file()
```

However predictor construction ignores `self._config_path` and calls:

```python
build_sam2(SAM21_CONFIG_ID, ...)
```

SAM 2's upstream `build_sam2()` treats this argument as a Hydra config name resolved from the installed SAM 2 package, not as the filesystem path checked by PackLab.

Consequences:

- a dummy unrelated file with the approved filename can make PackLab's config probe pass;
- the artifact PackLab says it validated can differ from the config SAM 2 actually executes;
- current tests intentionally create a fixture text file named `sam2.1_hiera_b+.yaml`, so they do not catch this disconnect.

Required correction:

- make the probed config identity and executed config identity one authoritative thing;
- for the approved SAM 2 runtime, prefer validating the packaged Hydra config from the verified SAM 2 installation/revision, including a deterministic config identity/digest or equivalent source-bound proof;
- remove the misleading external config-path sentinel if it is not the artifact SAM 2 executes;
- add a regression proving a lookalike/dummy config cannot satisfy production capability;
- provenance must record the actual executed config identity.

Upstream behavior reference:
https://github.com/facebookresearch/sam2/blob/2b90b9f5ceec907a1c18123530e92e794ad901a4/sam2/build_sam.py

## Criteria disposition

1. PASS — tracker authorization and scope were correct.
2. PASS — model-specific code remains behind the PackLab adapter.
3. PASS — frozen target model/checkpoint/config identifiers are correct.
4. PASS — checkpoint acquisition/hash/no-auto-download behavior is correct.
5. PASS — local-only runtime boundary is preserved.
6. **FAIL** — observed SAM 2 runtime revision/package identity is not measured; expected revision is emitted as if observed.
7. PASS — CUDA/CPU state is capability-shaped and no unsupported performance claim is made.
8. **CHANGES_REQUIRED** — provenance is strong for checkpoint/runtime device facts but not for actual SAM 2/config artifact identity.
9. PASS — point/box behavior is implemented; no unsupported automatic-mask claim is made.
10. PASS — tested malformed/missing/non-finite paths fail closed.
11. PASS — PL-0187 behavior is not included.
12. **CHANGES_REQUIRED** — missing regression coverage for mismatched installed SAM 2 identity and lookalike config identity.
13. PASS — no private/native model execution claim is made.
14. PASS — no unreviewed runtime wheels were injected into the canonical lock.
15. PASS as builder evidence for recorded checks; no audit acceptance due findings above.
16. PASS — protected lifecycle files were not edited by Codex.
17. PASS — implementation and log commits are separate.
18. PASS — log is structurally complete and ends correctly.

## Required remediation

Keep the accepted implementation intact except for the narrow runtime/config provenance boundary.

1. Add a runtime identity record separating expected identity from observed installed identity.
2. Never emit the frozen upstream SHA as an observed runtime revision unless independently proven from the installed runtime source/package.
3. Fail production capability closed when the approved SAM 2 runtime identity cannot be verified.
4. Bind the executed Hydra config to the same verified SAM 2 runtime identity.
5. Remove or redesign the external `config_path` sentinel so PackLab cannot validate one file while SAM 2 executes another.
6. Add tests for:
   - SAM 2 unavailable -> observed identity unavailable;
   - approved observed runtime identity -> available;
   - mismatched/unverified installed SAM 2 identity -> unavailable;
   - dummy/lookalike config file cannot make production capability available;
   - actual executed config identity is present in provenance;
   - all previously accepted checkpoint/prompt/mask/source-immutability behavior remains green.
7. Do not start PL-0187 or M09.

## Verdict

`CHANGES_REQUIRED`
