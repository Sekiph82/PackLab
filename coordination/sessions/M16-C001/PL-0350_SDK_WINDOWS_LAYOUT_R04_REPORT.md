# PL-0350 R04 Hosted Build Report

Date: 2026-10-13
Implementation SHA: `a2805616c9c0dd665e48b1de82c8436ea64b0805`
Hosted cold run: [38346317865](https://github.com/Sekiph82/PackLab/actions/runs/38346317865)
Result: **Stopped at first OCP runtime dependency ownership failure**

## What passed

- Local focused tests: **37 passed, 1 skipped**. Ruff, Ruff format, mypy (10 changed source files), compileall, workflow Python import smoke (16 modules), YAML parse, diff hygiene, and the synthetic no-native preflight all passed.
- Exact-SHA hosted preflight [38346246435](https://github.com/Sekiph82/PackLab/actions/runs/38346246435) passed the nested Windows SDK layout fixture. Producer seam, consumer validator, and downstream dependency scanner passed; native work was false; all SDK/OCP/Studio jobs were skipped.
- The one authorized cold run compiled and validated the OpenGL-enabled OCCT SDK in the canonical Windows hierarchy. SDK cache v4 missed, then the new SDK checkpoint was sealed, uploaded, and independently visible before OCP compilation.
- SDK artifact: ID `11790440856`, name `packlab-occt-sdk-38346317865-1`, 57,520,243 bytes, SHA-256 `467b44ab0fb747343cb55e55e71a0dd4ecadb989fd7eed22d1e49fff3153ddf8`.
- Source evidence artifact: ID `11790585684`, name `packlab-native-source-evidence-38346317865-1`, 1,398 bytes, SHA-256 `091c391b8d6ccda19823f57eae891b1dd45383b164c117ca05928df6bafd2018`.
- The OCP job verified the same-run SDK and source evidence, validated the official generated source ZIP, and correctly rejected the exact v4 OCP cache key as a cache miss. Native compile produced `OCP.cp312-win_amd64.pyd`.

## First blocker and exact boundary

The OCP job failed after the extension was compiled, during the builder’s post-build dependency ownership scan:

```text
ValueError: compiled OCP references an unowned DLL dependency: fmt.dll
```

The GitHub step ended with exit code 1. The Python builder rejected `fmt.dll` as not owned/declared. This was not an MSVC compile failure. The SDK checkpoint and source evidence artifacts remain preserved.

The first error skipped the remaining OCP checkpoint validation, native CAD/STEP smoke, runtime sealing/cache save/upload, and Studio packaging/smoke. No compliance clearance, unsigned Installer, or warm-cache run exists. No retry or additional build was authorized or performed in this pass.

## Handoff

**BATCH_STOPPED_AT_PL-0350 / OCP_NATIVE_DEPENDENCY_UNOWNED_FMT_DLL / AWAITING_INDEPENDENT_AUDIT**

Codex made no claim of PL-0350 acceptance. Root `TASKS.md` and ChatGPT audit records remain untouched. The required independent audit should inspect the implementation commit, [hosted preflight](https://github.com/Sekiph82/PackLab/actions/runs/38346246435), [cold run](https://github.com/Sekiph82/PackLab/actions/runs/38346317865), failed OCP job `115138281145`, and the artifact identities/digests recorded above.
