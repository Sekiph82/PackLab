# PL-0289 - ChatGPT Audit Criteria V01

Task: **Benchmark/select supported Python OpenCascade binding for Windows packaging**

All criteria are mandatory.

1. M13 tracker/master authorization, safe synchronization, M12 AUDITED_PASS, ADR-0005 and M09 deferral were read.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Evaluate current Python OpenCascade binding candidates against PackLab's actual Windows x86-64 / CPython 3.12 / uv environment. Candidate review must include at least the realistic pip/uv path and pythonocc-core as a comparison where feasible, but no package is preselected. Selection criteria: installability in the locked PackLab environment, successful import, exact OCCT/kernel version visibility, STEP/BREP/tessellation/boolean capability probes needed by M13, wheel/native artifact provenance, license of the binding itself, OCCT license/exception, transitive native contents, package size/redistribution attention, and compatibility with a PackLab-owned adapter. Pin exactly one supported binding only if the evidence is sufficient. If none passes, stop BLOCKED rather than inventing compatibility. No runtime auto-download or vendor binary fetch.
3. Tests/evidence cover at minimum: candidate matrix; exact selected package/version/build; Windows CPython 3.12 install/import; kernel/version probe; BREP/revolve/loft/boolean/tessellation/STEP capability smoke; wheel/native digest evidence; binding license separate from OCCT license; lockfile update; no runtime download; unavailable candidate reasons.
4. CAD/BREP remains derived from exact Design Model revision; parent authority, units and DEFERRED_OWNER_VALIDATION remain explicit; no RELATIVE->mm or unverified->physical/mold authority promotion occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced. PL-0289 alone owns dependency/lock/license selection.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log publication is separate; child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0289_CODEX_PROMPT_V01.md
