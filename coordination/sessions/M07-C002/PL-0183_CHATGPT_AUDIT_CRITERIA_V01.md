# PL-0183 - ChatGPT Audit Criteria V01

Task: **Convert final textured mesh to a PackLab-supported preview/export format without losing the master source**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0183_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. PL-0182 is validation-green and published before this child begins; live
   tracker authorization remains valid.
2. Only existing PackLab-supported formats are accepted, with explicit format
   validation and no unreviewed dependency/runtime addition.
3. Only coherent successful textured-mesh inputs are exportable; source,
   revision, request, configuration, and output identities are cross-checked.
4. Derived output and provenance/sidecar publication are deterministic and
   atomic, with collision and overwrite behavior explicit and safe.
5. Failed/cancelled/malformed input, unsupported format, unsafe/private path,
   source/output alias, collision, and injected publication failure are
   rejected without corrupting or replacing the master source or RAW_CAPTURE.
6. Provenance records source/output/configuration/format digests and truthful
   reconstruction-observation, scale, and non-Scan-Master limitations.
7. Tests are behavior-sensitive and cover supported success, rejection and
   failure-injection boundaries, source-byte preservation, and regression.
8. Required focused/full/static/security/scope checks and child log evidence
   pass truthfully; the log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.
