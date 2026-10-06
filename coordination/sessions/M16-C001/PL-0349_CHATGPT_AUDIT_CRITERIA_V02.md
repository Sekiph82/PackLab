# PL-0349 - ChatGPT Audit Criteria V02

Task: **Capability-complete frozen Windows Studio production build**

All criteria are mandatory.

1. Live TASKS authorization and M16 partial audit V03 are read; root TASKS is not edited by Codex.
2. The packaged production build includes the locked direct in-process runtime capabilities required by PackLab, including OCP/cadquery-ocp-novtk and Open3D 0.20.0.
3. Dynamic-import omissions are fixed through explicit reviewable packaging rules; capability probes are not weakened.
4. Frozen executable smoke proves Qt GUI startup plus PackLab OCP/CAD and Open3D capability availability with bounded real operations and no network/download.
5. Runtime completeness manifest is path-free, build/revision/version bound, and fails on missing required in-process capability.
6. Broad PySide meta/Addons surface is reduced to the minimal exact package set when source evidence permits; no production feature is removed merely to simplify licensing.
7. Repository-wide PackLab Qt imports are covered by an explicit module contract/test; unexpected Addons-only use fails the remediation rather than being hidden.
8. OCP/Open3D packaging excludes unrelated examples/tests/development assets where possible but includes required native/runtime files.
9. Blender/COLMAP/OpenMVS and private scans/checkpoints remain unbundled; no hidden runtime download is added.
10. Locked dependencies, Ruff/format, mypy, focused tests, full pytest, compile and privacy/scope checks pass.
11. Fresh hosted Windows build proves the capability-complete frozen bundle and records final staged file count/bytes for PL-0350.
12. Scope remains PL-0349 packaging completeness; no PL-0350 installer/compliance claim, PL-0351+, M17 or PL-0368 implementation.
13. Implementation/evidence and V02 log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0349_CODEX_PROMPT_V02.md
