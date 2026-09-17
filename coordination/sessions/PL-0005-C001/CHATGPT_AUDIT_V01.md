# PL-0005-C001 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Task: **PL-0005 — Create dependency/license register for NextLevel, COLMAP, OpenMVS, Open3D, OpenCV, PyTorch, OpenCascade bindings, Blender and PySide6.**

Audited range:
- frozen starting commit: `cb7a51e8b3d899e2ad8865f74fae634b7cda1ec1`
- implementation commit: `c4a2b3ff074c96eea2f23767c8b465f5b912b823`
- Codex log commit / audited head: `e2cb8567e606b2f828b155e7631a27386b1ef83c`
- prompt: `coordination/sessions/PL-0005-C001/CODEX_PROMPT_V01.md`
- frozen criteria: `coordination/sessions/PL-0005-C001/CHATGPT_AUDIT_CRITERIA_V01.md`
- implementer evidence: `coordination/sessions/PL-0005-C001/CODEX_LOG_V01.md`

## Executive result

The dependency/license register is substantively strong and passes the architecture, scope, provenance, license-description, risk-classification, distribution-scenario, compliance-checklist, privacy, and public-repository review portions of the frozen criteria.

However, V01 cannot close because two mandatory synchronization-evidence criteria were not satisfied exactly as frozen before material implementation:

- **Criterion 4 FAIL** — V01 required `git fetch origin main --prune` before material implementation. The Codex log explicitly states that the first pre-merge fetch omitted `--prune`. A later pre-push fetch with `--prune` cannot retroactively satisfy a criterion whose timing is explicitly before material implementation.
- **Criterion 5 FAIL** — V01 required an ahead/behind record before any merge. The Codex log explicitly states that the pre-merge relation was represented by two commit-hash queries rather than the required ahead/behind relation. The successful fast-forward is consistent with a behind-only state, but it is not the frozen evidence record itself.

Because all 165 frozen criteria are mandatory, these two failures require a remediation cycle even though no substantive register rewrite is currently required.

## Independent GitHub evidence reviewed

ChatGPT independently inspected:

- root `TASKS.md` authorization state for PL-0005;
- `CODEX_PROMPT_V01.md`;
- all 165 frozen `CHATGPT_AUDIT_CRITERIA_V01.md` items;
- `CODEX_LOG_V01.md`;
- `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`;
- implementation commit `c4a2b3ff074c96eea2f23767c8b465f5b912b823`;
- actual GitHub `main` head `e2cb8567e606b2f828b155e7631a27386b1ef83c`;
- exact compare `cb7a51e8...e2cb8567`.

The compare contains exactly two added files:

1. `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`
2. `coordination/sessions/PL-0005-C001/CODEX_LOG_V01.md`

No tracker, existing architecture artifact, prior session artifact, application/source/schema/runtime file, dependency lock file, package manifest, or PL-0006+ implementation was changed by Codex in the audited range.

## Independent contemporary license verification

The material license claims were independently checked against authoritative upstream sources rather than accepted from the Codex summary.

### NextLevel

**PASS.** Upstream `NextLevel/NextLevel` LICENSE is MIT. The register correctly limits that statement to NextLevel itself and leaves future Swift/transitive contents for later review.

### COLMAP

**PASS.** The official COLMAP license page states that COLMAP itself uses the new BSD license and explicitly says third-party dependencies are separately licensed and can affect the resulting build/license analysis. The register preserves this distinction and does not treat BSD as blanket binary clearance.

### OpenMVS

**PASS.** Canonical `cdcseacave/openMVS` license evidence is GNU AGPL v3. The register correctly marks OpenMVS **HIGH LICENSE ATTENTION** and avoids unsupported conclusions about a future closed-source/commercial/bundled/network deployment.

### Open3D

**PASS.** Canonical Open3D LICENSE is MIT. The register also preserves third-party/build review instead of flattening a future shipped build to only the primary MIT license.

### OpenCV

**PASS.** OpenCV's official license page states that 4.5.0 and higher use Apache License 2.0 and 4.4.0 and lower use 3-clause BSD. Because PackLab has not pinned a version, preserving the version split is correct.

### PyTorch

**PASS.** Current upstream `pyproject.toml` explicitly says the main PyTorch project license is BSD-3-Clause and gives a broader SPDX expression for installed package contents, with third-party license files included. The register correctly separates main-project licensing from package/transitive contents.

### Open CASCADE Technology (OCCT)

**PASS.** Canonical OCCT evidence identifies LGPL 2.1 plus the Open CASCADE special exception. The register correctly keeps OCCT licensing separate from the Python binding layer and does not claim a commercial route has been selected.

### Python OpenCascade binding

**PASS.** Final binding remains `TBD / NOT SELECTED` and PL-0289 retains selection authority. `pythonocc-core` is only a candidate example; its own upstream LICENSE is LGPL v3. The register does not incorrectly assign OCCT's license to every binding.

### Blender

**PASS.** Blender's official license guidance identifies Blender as GPL software, source developed at blender.org generally as GPL-2.0-or-later, compatible binary distribution under GPLv3-or-later, published Blender-API Python add-ons/scripts as requiring GPL-compatible terms, and user-created artwork/output as belonging to the creator. The register represents these distinctions conservatively.

### PySide6 / Qt for Python

**PASS.** Official Qt for Python documentation states that the project is available under LGPLv3/GPLv3 and the Qt commercial license. The register correctly treats module/component/package selection as later distribution-sensitive work and does not claim a commercial license has been purchased.

## Frozen-criteria disposition

- Criteria **1–3:** PASS based on Codex local evidence and repository identity.
- Criterion **4:** **FAIL** — pre-implementation fetch omitted `--prune`.
- Criterion **5:** **FAIL** — no explicit ahead/behind relation was recorded before the merge as frozen.
- Criteria **6–165:** PASS, subject to the normal evidence limitation that ChatGPT cannot independently rerun the historical local Windows/Git shell commands from this audit environment.

Substantive result: **163 / 165 mandatory criteria pass.**

Process result: **2 / 165 mandatory criteria fail.**

Overall V01 decision therefore remains **CHANGES_REQUIRED**.

## Security / privacy review

**PASS.** No secrets, credentials, Apple signing material, private keys, private Kenya scans, confidential supplier content, proprietary production artwork, machine serials, network identifiers, or other protected content were found in the audited Codex range.

## Architecture review

**PASS.** The register preserves PackLab-owned adapter boundaries, does not turn license integration modes into legal conclusions, keeps PySide6 and Blender away from domain/dimensional truth, preserves Scan Master / Design Model ownership, and introduces no ADR-worthy architecture change.

## Required remediation

No substantive dependency/license-register content change is required by this V01 audit.

V02 must:

1. synchronize from the current GitHub `main` using the exact safe sequence before any V02 material work;
2. run and record `git fetch origin main --prune`;
3. run and record `git rev-list --left-right --count HEAD...origin/main` before any merge;
4. stop on unexpected tracked changes, ahead/diverged state, or repository mismatch;
5. prove local HEAD equals `origin/main` before V02 validation work;
6. re-read the existing register and rerun the required content/scope validation without changing it unless a new defect is discovered;
7. add only `coordination/sessions/PL-0005-C001/CODEX_LOG_V02.md` if no register correction is needed;
8. push safely and return `AWAITING_AUDIT`.

## Coordinator instruction

- Keep `PL-0005` unchecked.
- Set H!veAI current task state to `CHANGES_REQUIRED`.
- Point Next Task/Action to `coordination/sessions/PL-0005-C001/CODEX_PROMPT_V02.md` and its matching criteria.
- Do not advance to PL-0006.
