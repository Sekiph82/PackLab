# PL-0183 - Codex Work Order V01

Task: **Convert final textured mesh to a PackLab-supported preview/export format without losing the master source**

Repository: https://github.com/Sekiph82/PackLab  
Cycle: `M07-C002`

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0183_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0183_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0183_CODEX_LOG_V01.md

## Authorization and predecessor gate

Start only after PL-0182 is validation-green and its log is remotely visible
inside the authorized M07-C002 batch. Re-read the live tracker, all rules,
the accepted M07 stage/retention/cancellation evidence, the existing texture
export contract, viewport-supported formats, provenance, and project-layout
boundaries. Stop on mismatch or an unsupported-format specification conflict.

## Frozen scope

Implement the PackLab-owned derived export/preview boundary for a successful
final textured-mesh result. Use only formats already supported by the existing
repository contracts (currently the texture boundary permits `ply`, `obj`,
`glb`, and `gltf`; the viewport boundary may support a narrower preview set).
The boundary must:

1. validate that the input is a coherent successful textured-mesh result with
   matching source/revision/request/configuration identity;
2. produce a deterministic, typed derived output plus provenance that records
   source identity, format/configuration, digests, authority class, scale
   limitation, and conversion/export identity;
3. publish output and sidecar/manifest atomically below a safe derived
   destination, preserving the textured master source and RAW_CAPTURE bytes;
4. reject failed/cancelled/malformed input, unsupported formats, unsafe or
   private paths, source/output identity aliasing, collisions, and ambiguous
   overwrite requests;
5. preserve the architecture distinction: this is reconstruction observation
   or preview/export evidence, not Scan Master, metric, CAD, BREP, or
   engineering authority.

Do not silently parse or alter geometry beyond the explicitly implemented
supported conversion, claim visual/metric quality without evidence, or add
third-party model/runtime dependencies.

## Allowed change boundary

- existing `core/src/packlab_core/texture_reconstruction.py` only for the
  minimal export seam, or one dedicated core export module;
- existing Studio viewport/project-layout/provenance seam only when required
  for the supported preview publication;
- dedicated export/preview/provenance tests;
- `coordination/sessions/M07-C002/PL-0183_CODEX_LOG_V01.md`.

Do not edit `TASKS.md`, ChatGPT artifacts, schemas, dependencies/locks,
accepted audits, RAW_CAPTURE/master source, private/generated reconstruction
media, PL-0184/M08 or later code, or unrelated viewport export behavior.

## Required validation and handoff

Run focused export/texture/viewport/provenance suites, exact locked full
pytest, Ruff/format, targeted mypy, compileall, diff/protected/scope,
dependency/privacy/secrets/generated/binary, and remote checks. Include
source-byte preservation, atomic-failure, unsupported/collision, and
provenance/determinism tests. Use separate implementation and log-only
commits; end the child log exactly with `READY_FOR_INDEPENDENT_AUDIT`.
After the final child, create the completed master log and end it exactly with
`AWAITING_MILESTONE_AUDIT`; do not start M08.
