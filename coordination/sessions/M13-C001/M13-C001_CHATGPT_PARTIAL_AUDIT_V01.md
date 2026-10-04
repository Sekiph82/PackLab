# M13-C001 - ChatGPT Partial Milestone Audit V01

Date: 2026-10-04  
Accepted frontier: **PL-0289 through PL-0298**  
Blocked frontier: **PL-0299 V01 authority conflict**  
Decision: **AUDITED_PARTIAL_CHANGES_REQUIRED**

## Accepted children

PL-0289 through PL-0298: **10/10 AUDITED_PASS**

The selected OpenCascade stack is accepted for M13 source development with one retained release gate:

- `cadquery-ocp-novtk==7.9.3.1.1`;
- Windows x86-64 / CPython 3.12;
- observed OCP 7.9.3.1 / OCCT 7.9.3;
- PackLab CAD adapter boundary enforced;
- native per-DLL license/NOTICE/redistribution inventory remains required before installer/binary redistribution.

This retained release gate does not authorize or block ordinary M13 source execution.

## PL-0299 blocker review

The builder stop is **valid**.

The mandatory M12 pre-read `assembly_hierarchy_export.py` is explicitly metadata-only and states:

- geometry is not embedded;
- CAD geometry is not exported;
- the handoff targets a future component-capable exporter.

PL-0299 V01 simultaneously required multipart OBJ and assembly hierarchy behavior. No exact M13 component geometry payload contract existed. Implementing assembly output from metadata alone would require inventing geometry/placement authority; failing the multipart requirement would violate the frozen child criteria.

Stopping before implementation was therefore correct.

## Resolution

PL-0299 V02 narrows the mandatory scope to **one exact Design Model/CAD PREVIEW_PROXY source at a time**:

- deterministic OBJ;
- deterministic GLB;
- stable semantic part name;
- explicit unit/scale-transform metadata;
- exact Design Model/CAD/parent authority;
- RELATIVE and mm_unverified both supported without authority escalation;
- no assembly geometry fabricated from metadata-only handoff.

Multipart/assembly OBJ/GLB becomes **conditional only** on a future/explicit source contract that supplies exact component geometry plus placement transforms. The existing M12 metadata-only hierarchy is not sufficient and must fail closed if passed as geometry source.

PL-0300 through PL-0309 remain unchanged and may proceed after PL-0299 V02 closes green.

## Verdict

`AUDITED_PARTIAL_CHANGES_REQUIRED`

M13 remains open. Resume at PL-0299 V02.
