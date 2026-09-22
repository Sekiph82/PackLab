# PL-0056 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0056_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0056_CHATGPT_AUDIT_CRITERIA_V01.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0056_CODEX_LOG_V01.md

Audited implementation commit: `f6b6b1fc0c9c38a71a8c46f6c0c2a3eb0e1a79bf`

## Blocking finding

The Python validator does not validate manifests against the frozen JSON Schema. Instead, `_validate_manifest` manually reimplements only part of `schemas/packscan/manifest.schema.json`.

That duplicate implementation is already weaker than the canonical schema. Examples that the frozen JSON Schema rejects but the Python validator accepts include:
- empty `device.model` despite schema `minLength: 1`;
- arbitrary `device.os_version` strings despite the frozen version regex;
- incomplete validation of `device_identifier`, `lens`, `source_evidence.provenance`, generic `media_type`, and `calibration_profile_ref`.

This creates a second, drifting source of truth and violates the requirement that Python read/write/validate operate against the frozen M02 schemas.

## Criterion disposition

1-6: PASS  
7: **FAIL** — Python validation is not actually driven by the frozen schema contract.  
8-10: PASS  
11: **FAIL** — canonical schema rules are effectively weakened in the Python path.  
12: **FAIL** — public fixture coverage does not detect schema/validator drift cases such as empty model or malformed OS version.  
13: **FAIL** — the implementation permits contract drift across ownership boundaries.  
14-18: PASS  
19: **FAIL** — the log claims schema-hardening stronger than the actual implementation.

Result: **14 / 19 PASS, 5 FAIL**

## Required remediation

Use the committed Draft 2020-12 JSON Schemas as canonical validation input in the Python validator, or generate one validator from those schemas without manually duplicating field rules.

At minimum:
- validate `manifest.json` with the actual frozen manifest schema;
- validate checksum/control JSON with their actual schemas;
- map schema failures into stable `PackScanError` codes without weakening schema semantics;
- preserve the existing ZIP/path/checksum/size integrity checks;
- add regression cases proving values rejected by the schema are also rejected by `validate_packscan`, including empty device model, malformed OS version and invalid optional fields.

Decision: **CHANGES_REQUIRED**
