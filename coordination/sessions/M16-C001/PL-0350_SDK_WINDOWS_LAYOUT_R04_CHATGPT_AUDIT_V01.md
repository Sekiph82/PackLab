# PL-0350 R04 — ChatGPT Independent Audit V01

Date: 2026-10-13
Verdict: **AUDITED_PARTIAL_CHANGES_REQUIRED**
First hard stop: **OCP_NATIVE_DEPENDENCY_UNOWNED_FMT_DLL**
Parent PL-0350: **OPEN / NO INSTALLER**

## Independent evidence

- Implementation SHA: https://github.com/Sekiph82/PackLab/commit/a2805616c9c0dd665e48b1de82c8436ea64b0805
- R04 Codex report: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_SDK_WINDOWS_LAYOUT_R04_REPORT.md
- R04 Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_SDK_WINDOWS_LAYOUT_R04_CODEX_LOG.md
- Updated master handoff: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md
- Hosted preflight https://github.com/Sekiph82/PackLab/actions/runs/38346246435
- Cold source build https://github.com/Sekiph82/PackLab/actions/runs/38346317865 ; OCP failure job https://github.com/Sekiph82/PackLab/actions/runs/38346317865/job/115138281145
- Producer code: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/build_controlled_ocp_from_generated_sources.py
- Existing native build lock: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/packlab-ocp-bindings-win.lock
- Current source lock: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/windows_native_source_lock.json
- OCP native manifest validator: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/validate_controlled_ocp_manifest.py
- Distribution inventory: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/windows_redistribution_inventory.py

Auditor independently retrieved full GitHub job table, relevant failed OCP job logs, actual artifact API metadata, source-built OCP code, native conda lock, source lock, manifest and inventory code. User's local test results, free disk and owner checkout protection were reviewed in Codex evidence, not independently rerun on the user's machine.

## Findings

**R04-01 PASS: source-pinned canonical Windows OCCT SDK build and artifact.** The actual cold run completed capacity stage and OCCT SDK stage; nested `win64/vc14` layout passed and an OpenGL-enabled, No-VTK OCCT SDK was sealed and uploaded *before* OCP compilation. Live GitHub Actions artifact identities independently match builder report:
- **SDK artifact ID 11790440856**, `packlab-occt-sdk-38346317865-1`, **57,520,243 bytes**, SHA-256 **467b44ab0fb747343cb55e55e71a0dd4ecadb989fd7eed22d1e49fff3153ddf8**.
- **Source evidence artifact ID 11790585684**, `packlab-native-source-evidence-38346317865-1`, **1,398 bytes**, SHA-256 **091c391b8d6ccda19823f57eae891b1dd45383b164c117ca05928df6bafd2018**.
- Both unexpired on audit; **both scheduled to expire 2026-10-14 05:03 UTC** under one-day artifact retention. The GitHub *archive* SHA is not the SDK inner manifest SHA. Future jobs MUST validate SDK per-file manifest/source/compiler/CMake options and preserve/extend checkpoint before expiry; do not treat mere archive name as proof.

**R04-02 PASS: actual 315-source OCP extension compiled/link success.** Real native MSVC job log includes `OCP.vcxproj -> .../Release/OCP.cp312-win_amd64.pyd` at **2026-10-13 07:07:31 UTC**. The OCP C++ stage *compiled*; this does not imply runtime linkage/import, CAD/STEP functional tests, sealed binary, or distribution pass.

**R04-03 HARD BLOCK: real PE dependency scan rejected unowned `fmt.dll`.** At **07:07:34 UTC**, after producing the Pyd, `build_controlled_ocp_from_generated_sources.py` failed at:
`ValueError: compiled OCP references an unowned DLL dependency: fmt.dll`.
The code loads direct and transitive PE imports with LIEF and accepts OS external runtime or an OCCT SDK DLL. **It currently treats every included native DLL as OCCT-owned**, with only OCP/OCCT source IDs permitted downstream. `fmt.dll` is neither a proven Windows System32 DLL nor included in the OCCT SDK DLL map. *Do not* whitelist `fmt.dll` as OS-provided or relabel it OCCT-owned. Need exact third-party owner/source/version/license notices and staged dependency closure.

**R04-04 highly relevant verified source evidence:** checked-in conda-forge `packlab-ocp-bindings-win.lock` ALREADY pins native **`fmt==12.1.0`** win-64 from `fmt-12.1.0-h1ced75a_1.conda`, exact conda SHA256 **1d6d6f1bf284e50cf617ce9a6250e0bf70bd0d30b068568364d6b1852aad9466**. This makes a plausible build-environment source for `fmt.dll`, **not a proven byte-level link** between that exact DLL and built OCP until real host inventory/hashes/import graph are verified. Existing `windows_native_source_lock.json` has **no explicit fmt source/notice record**. Existing validators and redistribution inventory accept ONLY the two native OCP/OCCT source IDs. Therefore fixing just PE scanning will be insufficient: full manifest, runtime staging, downstream inventory and corresponding source/license map require an explicit fmt owner model, plus review any additional transitives.

**R04-05 PASS: safety-first stopping boundary.** Cold OCP job failed, Studio job skipped. No OCP runtime bundle, cache, source/notice engineering clearance, unsigned installer, cold acceptance or warm HIT. No blind retry. Builder-reported tests 37 PASS, 1 SKIP (Windows symlink privilege), Ruff, formatting, targeted mypy, compileall, 16 module imports, YAML parse, and diff hygiene. No full-suite rerun this R04.

## Next repair priorities / cost containment

1. **Urgent checkpoint preservation before expiration:** audit the current same-run SDK and source evidence and, using a bounded **noncompiling** manual hosted action, validate origin artifact digests AND sealed inner OCCT SDK file manifest/source lock/toolchain/OPENGL=ON/VTK=OFF; republish/extend artifact under explicit provenance to durable retention or validated controlled cache **without recomputing OCCT** if supported. Do not delete/change prior artifacts or bypass GitHub retention/storage guard. No native OCP compile just to copy/checkpoint SDK. If preserving before expiry is impossible, record that precisely.
2. **No OCP repeat before third-party closure:** perform fresh-host read-only conda inventory for exact locked fmt 12.1.0 binary (path, SHA, exports/imports, package metadata), and entire dependency graph for OCP and OCCT plus Windows system runtimes. Source record for fmt needs exact upstream corresponding sources and documented license/notice availability, verified immutable SHA; never fabricate archive hashes or list wheel DLLs under OCCT.
3. Extend builder, SDK/OCP source-manifest schema, runtime bundle validator/redistribution inventory and packaging to **fail-closed OWN fmt.dll separately** (and any additional DLL transitives) by a real exact-lock proven component with full hash/byte/notice/source evidence. Test all acceptance and tampered/missing/unknown DLL denial; no `fmt.dll` OS-runtime exemption, broad allowlist, or forced static-link switch without separately audited architecture.
4. Add a cheap hosted *precompile dependency-ownership closure gate* that inventories CMake imported link targets and exact conda/native dependency DLLs, optionally representative small PE link fixture, so no further 2-hour OCP compilation starts with an already known unowned fmt dependency. Consider preserving a quarantined source-built OCP Pyd with hash/source identity and no production deployment **immediately after build/link** and before ownership scan, to avoid losing two hours on a provenance-only failure. Such quarantine is not an approved runtime nor an installer.
5. SDK cache key is currently sensitive to whole `.github/workflows/windows-studio-build.yml` via `hashFiles`, so any R05 workflow change likely forces a new SDK cache key. Plan a source/toolchain/SDK-only stage key and explicit provenance-checked reuse of live R04 SDK artifact under a new run/manifest to avoid another ~40min source compile; an unverified cross-run artifact copy would weaken checkpoint identity rules. Source lock, native Python 3.12.15, 315 No-VTK modules, 4 workers, manual-only CI, zero source/license notice blockers and owner Desktop protection unchanged.

Disposition: **AUDITED_PARTIAL_CHANGES_REQUIRED / OCP_NATIVE_DEPENDENCY_UNOWNED_FMT_DLL**. PL-0350 remains OPEN and PL-0351, M17 and PL-0368 remain blocked.

Focused R05 implementation and matching audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_FMT_DEPENDENCY_PROVENANCE_R05_CODEX_PROMPT.md
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_FMT_DEPENDENCY_PROVENANCE_R05_CHATGPT_AUDIT_CRITERIA.md
