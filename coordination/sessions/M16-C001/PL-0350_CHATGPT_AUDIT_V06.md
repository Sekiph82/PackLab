# PL-0350 - ChatGPT Independent Audit V06

Date: 2026-10-09
Decision: **AUDITED_CHANGES_REQUIRED**
Task: **Provenance-complete controlled OCP/OCCT Windows runtime + final redistribution closure**

## Evidence inspected

- Active R07 master:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_OWNER_EXE_REPAIR_PL0350_V06_CONTINUATION_CODEX_PROMPT_V11.md
- PL-0350 V06 prompt:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V06.md
- Hosted Windows quality run:
  https://github.com/Sekiph82/PackLab/actions/runs/37860820227
- Hosted Windows production run:
  https://github.com/Sekiph82/PackLab/actions/runs/37860820132
- Source commit:
  https://github.com/Sekiph82/PackLab/commit/961591d990b32650f5258f232dabdf0e9686e84d
- Current controlled runtime builder:
  https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/build_controlled_ocp_runtime.py
- Current production workflow:
  https://github.com/Sekiph82/PackLab/blob/main/.github/workflows/windows-studio-build.yml
- Pinned upstream OCP build definition:
  https://github.com/CadQuery/OCP/blob/d69b064a3a604ebf245b1f3b14fb54c835a3a571/CMakeLists.txt
- Pinned upstream pywrap CLI:
  https://github.com/CadQuery/pywrap/blob/92519409a57f9ec3f2c005b8057006fdb4752c23/bindgen/__main__.py

## Accepted evidence

The Windows quality run is green on the same source commit.

The V06 source/package provenance direction remains accepted:

- exact OCP source revision is pinned;
- exact pywrap source revision is pinned;
- exact OCCT 7.9.3 source revision is pinned;
- corresponding-source archives are hash-verified before build;
- no opaque third-party wheel provenance is being guessed;
- the controlled runtime builder creates a file-level manifest.

The owner Desktop `PackLab.exe` path is independently healthy for OWNER DEV use. It remains distinct from installer portability.

## Hosted blocker

The production job did not fail from a compiler error.

GitHub canceled the job after approximately six hours while the controlled OCP wrapper generator was still progressing.

The exact final observed pywrap progress was:

- **276 / 319 modules**
- approximately **87%**
- no fatal compiler/bindgen error preceded cancellation.

The job therefore never reached:

- PackLab production staging;
- frozen Qt/PDF/OCP/Open3D smoke;
- redistribution inventory;
- clearance;
- installer generation.

No PL-0351 execution is authorized from this run.

## Root cause

The current production workflow rebuilds the entire controlled OCP/OCCT runtime inside the same packaging job.

The pinned OCP CMake contract defines:

`set(N_PROC 2 CACHE STRING "Number of processes used for generating code")`

and invokes bindgen with:

`-n ${N_PROC}`.

PackLab V06 does not override `N_PROC`, so pywrap generation runs with two joblib workers even though the hosted Windows runner can safely use a bounded four-worker contract.

The same expensive controlled runtime is also rebuilt from scratch for every workflow run even when the exact native source lock/build inputs have not changed.

This is operationally incompatible with GitHub-hosted job duration limits.

## Required V07 remediation

V07 must preserve the exact provenance model while changing CI architecture:

1. build the controlled OCP/OCCT runtime in a **dedicated job** separate from PackLab packaging;
2. set and record a bounded **OCP bindgen worker count of 4**;
3. produce a sealed controlled-runtime bundle + manifest;
4. cache that bundle across workflow runs using a key derived from the exact native build contract;
5. validate every restored cache file against the manifest and source-lock digest before use;
6. publish the bundle as a same-run short-lived artifact for the packaging job;
7. make the packaging job consume the verified bundle rather than rebuilding OCP/OCCT;
8. keep package/frozen-runtime/redistribution/installer gates unchanged.

A cache hit must never bypass provenance validation.

## Verdict

`AUDITED_CHANGES_REQUIRED`

Resume with **PL-0350 V07**. PL-0351 remains blocked until PL-0350 produces a cleared unsigned installer.
