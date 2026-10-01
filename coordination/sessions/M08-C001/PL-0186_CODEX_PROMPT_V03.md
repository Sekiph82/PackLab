# PL-0186 — Codex Remediation Work Order V03

Task: **Fix SAM 2.1 runtime identity and executed-config provenance**

Repository:
https://github.com/Sekiph82/PackLab

Branch:
`main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Source audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_V01.md

V03 audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_CRITERIA_V03.md

Owner decision:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0004-sam2.1-segmentation-backend.md

Mandatory backend contract:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md

Required V03 log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CODEX_LOG_V03.md

## Authorization gate

Before material work:

1. `git fetch origin main --prune`
2. inspect `git status --porcelain`
3. inspect `git rev-list --left-right --count HEAD...origin/main`
4. fast-forward only when safe

The live tracker must authorize:
- M08
- M08-C001
- PL-0186 V03
- CHANGES_REQUIRED
- CODEX
- PL-0187+ and M09 unauthorized

Otherwise stop `TASK_STATE_MISMATCH`.

Do not edit `TASKS.md`, ADR-0004, ChatGPT audits/criteria, accepted predecessor evidence or later tasks.

## Preserve accepted V02 behavior

Do not redesign unrelated accepted code.

Preserve:
- exact SAM 2.1 Hiera Base+ owner selection;
- exact checkpoint source/filename/size/SHA-256 gate;
- no checkpoint/model binary in Git;
- no hosted API;
- no application-time download fallback;
- local runtime adapter boundary;
- point prompt;
- box prompt;
- source-grid mask normalization;
- malformed output/confidence failure behavior;
- immutable source bytes;
- PL-0187 post-processing remains untouched.

Checkpoint constants remain:

```text
sam2.1_hiera_base_plus.pt
323606802 bytes
a2345aede8715ab1d5d31b4a509fb160c5a4af1970f199d9054ccfb746c004c5
```

## Finding A — expected SAM revision is currently masquerading as observed runtime revision

Current V02 initializes:

```python
self._sam2_revision = SAM21_UPSTREAM_REVISION
```

and `probe()` returns it regardless of what local SAM 2 package is actually importable.

Fix this.

Required model:

```text
approved/expected identity != observed installed identity
```

The capability/provenance boundary must record both separately.

At minimum expose:
- approved upstream repository;
- approved source revision;
- observed SAM 2 availability;
- observed package/version/source form;
- observed module path;
- observed source revision when it can be proven;
- whether observed identity matches approved identity;
- explicit reason when identity cannot be verified.

Do not claim `2b90b9f...` as an observed installed revision merely because PackLab expects it.

### Runtime identity policy

Choose one deterministic supported local runtime form and document it.

A preferred safe policy is:

**verified source checkout / editable install at the approved SAM 2 commit**

For that form:
- locate the imported `sam2` module;
- resolve the owning source checkout/repository;
- verify the actual git commit equals `2b90b9f5ceec907a1c18123530e92e794ad901a4`;
- report the observed path only as machine-local diagnostic, not portable project truth;
- capability is unavailable when the commit cannot be proven or mismatches.

If you instead support a packaged wheel/sdist form, prove its package version and source correspondence to the approved revision with deterministic evidence. Do not infer commit identity from a filename/version string alone.

Tests must use fake identity providers rather than requiring git/PyTorch in the normal suite.

When SAM 2 is not installed, observed identity must say unavailable. It must not contain the frozen commit as though observed.

## Finding B — probed config file differs from the config actually executed

V02 validates `self._config_path`, but predictor creation executes:

```python
build_sam2(SAM21_CONFIG_ID, ...)
```

Upstream SAM 2 resolves that as a Hydra config name from the installed SAM 2 config search path. The arbitrary filesystem `config_path` is therefore not the executed config.

Fix this so there is **one config authority**.

Preferred design for the approved source-checkout runtime:

1. derive the packaged/config source root from the verified imported SAM 2 checkout;
2. resolve the exact approved config:
   `sam2/configs/sam2.1/sam2.1_hiera_b+.yaml`
   or the actual package-resource equivalent for that verified revision;
3. compute a deterministic identity/digest for that exact config file;
4. record config ID + digest in capability/provenance;
5. call `build_sam2(SAM21_CONFIG_ID, ...)` only after proving the installed Hydra config with that ID is the verified artifact from the approved runtime source.

If an external `config_path` is no longer meaningful, remove it from the production authority surface or clearly demote it from authority. Do not retain a dummy sentinel that can make capability pass.

A lookalike file named `sam2.1_hiera_b+.yaml` outside the verified runtime must not satisfy production capability.

## Failure behavior

Production capability must fail closed when:
- SAM 2 unavailable;
- observed runtime identity unavailable/unverifiable;
- observed runtime revision mismatches approved revision;
- approved config cannot be resolved from the verified runtime;
- config digest/identity does not match expected source-bound identity;
- checkpoint missing/mismatched;
- PyTorch/torchvision unavailable;
- requested device unavailable.

No failure path may emit a valid-looking mask.

## Tests

Add/adjust tests that prove:

1. SAM 2 unavailable -> observed identity unavailable, not frozen revision.
2. Verified approved source runtime -> identity match true.
3. Mismatched source commit -> backend unavailable.
4. Unverifiable runtime source -> backend unavailable.
5. Lookalike external config file -> cannot make backend available.
6. Verified executed Hydra config identity/digest appears in provenance.
7. Checkpoint exact identity/hash remains accepted.
8. Wrong checkpoint remains rejected.
9. Point/box segmentation regressions stay green.
10. Coordinate transform/source-grid behavior stays green.
11. Malformed/non-finite model output stays fail-closed.
12. RAW_CAPTURE/source bytes remain immutable.
13. No network/download fallback exists.
14. Fake runtime seam remains sufficient for normal tests without installing PyTorch/SAM 2.

## Validation

Run:
- PL-0186 focused tests;
- PL-0184/PL-0185 regressions;
- exact locked full pytest suite;
- Ruff;
- format check;
- targeted/relevant mypy;
- compileall;
- `git diff --check`;
- protected-file/scope review;
- dependency/license review;
- privacy/secrets/signing review;
- generated/binary review;
- remote visibility/freshness checks.

Report pre-existing unrelated debt truthfully without changing unrelated files.

## Publication

Create:
1. implementation/evidence commit(s);
2. separate log-only commit:
   https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CODEX_LOG_V03.md

The log must record:
- synchronized starting SHA;
- implementation SHA(s);
- exact runtime identity verification method;
- expected vs observed runtime fields;
- config authority and digest strategy;
- focused/full/static results;
- changed files;
- residual limitations;
- remote evidence.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Stop. Do not start PL-0187 or M09.
