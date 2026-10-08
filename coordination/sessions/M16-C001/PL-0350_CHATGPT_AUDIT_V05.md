# PL-0350 - ChatGPT Independent Audit V05

Date: 2026-10-08
Decision: **AUDITED_CHANGES_REQUIRED**
Task: **Windows installer redistribution/source-evidence closure**

## Evidence inspected

- PL-0350 V05 prompt and criteria.
- Hosted production run:
  https://github.com/Sekiph82/PackLab/actions/runs/37744258521
- Exact pre-clearance artifact:
  https://github.com/Sekiph82/PackLab/actions/runs/37744258521/artifacts/11534574864
- Current repository redistribution evidence and V05 Codex log.
- Exact downloaded artifact contents:
  - `compliance-validation.json`;
  - `windows-component-summary.json`;
  - `windows-redistribution-inventory.json`;
  - license/notice evidence.

## Hosted result

The hosted Windows production job passed:

- source checkout / Python / locked dependency setup;
- production one-directory staging;
- approved Qt staged-surface assertion;
- frozen no-network PackLab Studio capability smoke;
- exact staging inventory;
- pre-clearance evidence publication.

It failed only at `Enforce redistribution clearance`, which is correct fail-closed behavior.

Exact hosted state for build revision `68ead2cd8074ec67ae018ceb7ef88ad27d1313d2`:

- staged files: **511**;
- staged bytes: **531,590,047**;
- unresolved shipped-file rows: **115**;
- unresolved components: **5**;
- unresolved items: **6**;
- missing source-package evidence: **5**;
- missing notice sets: **0**;
- forbidden Qt components: **0**;
- external prerequisites: **1**;
- engineering status: `BLOCKED`;
- legal review required: `true`;
- public release authorized: `false`.

Exact unresolved items:

1. `component:cadquery-ocp-novtk`;
2. `component:open3d`;
3. `component:pyside6-addons`;
4. `component:pyside6-essentials`;
5. `component:shiboken6`;
6. `evidence:missing-source-packages`.

## Root finding

V05 correctly refused to invent exact native provenance for the opaque prebuilt `cadquery-ocp-novtk==7.9.3.1.1` wheel.

The pinned OCP source recipe establishes OCCT 7.9.3 but resolves the native environment using a broad `occt=7.9.3=all*` selection. The repaired wheel contains bundled third-party native DLLs, while its DELVEWHEEL metadata does not provide a complete exact source/version manifest for those bundled DLLs.

Therefore continuing to reverse-infer exact source versions from file names would violate the accepted no-guessing rule.

## Required next strategy

PL-0350 V06 must stop trying to certify the opaque OCP wheel retrospectively.

The preferred engineering route is a **PackLab-controlled provenance-complete OCP/OCCT runtime build**:

- pinned OCP source revision;
- pinned OCCT 7.9.3 source;
- exact native dependency package/build lock;
- authoritative source/package URLs + SHA-256;
- machine-readable file-to-source/license mapping;
- reproducible hosted build/staging proof.

Qt/PySide/Shiboken and Open3D source/notice evidence should be closed in the same V06 cycle once the native source-evidence model is in place.

## Verdict

`AUDITED_CHANGES_REQUIRED`

Resume with PL-0350 V06. PL-0351 remains blocked until an unsigned cleared installer exists.
