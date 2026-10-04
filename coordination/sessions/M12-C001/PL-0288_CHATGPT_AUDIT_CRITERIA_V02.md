# PL-0288 - ChatGPT Audit Criteria V02

Task: **Add package-family conversion safeguards across both parent authority modes**

All criteria are mandatory.

1. R02 tracker/master authorization, safe synchronization, M12 partial audit V02 and ADR-0005 were read.
2. Implementation is deterministic and limited to: Implement intentional versioned family conversion across bottle/jar, jerrycan, tube and flexible-pack families. Conversions preserve the original revision and exact parent-authority mode. Semantic mapping must be explicit; unsupported features are reported and never silently discarded. Converting a standalone model must not invent Scan Master ancestry; converting a scan-bound model must not drop its exact captured parent. Cross-authority conversion/rebinding is out of scope unless an explicit reviewed operation exists.
3. Tests/evidence cover at minimum: same-family no-op; explicit semantic mapping; unsupported feature report; original preservation; scan-bound parent preserved; standalone root preserved; cross-authority silent conversion rejected; deterministic conversion revision.
4. CAPTURED_SCAN_MASTER and STANDALONE_DESIGN_GEOMETRY are explicit, discriminated and never faked or silently interchanged.
5. Existing scan-bound Design Model revision identity/serialization compatibility remains intact; standalone parents carry no fabricated scan-specific ancestry.
6. Scale/unit/deferred-validation authority is honest: no METRIC_VERIFIED, captured, physical, mold or manufacturing claim is invented.
7. No M13 CAD/BREP/OpenCascade/STEP work, unreviewed dependency/private evidence or later-scope implementation is introduced.
8. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; V02 log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0288_CODEX_PROMPT_V02.md
