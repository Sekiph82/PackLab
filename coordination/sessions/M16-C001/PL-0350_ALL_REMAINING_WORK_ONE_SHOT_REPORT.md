# PL-0350 One-Shot Final Result Report

## Disposition

**ENGINEERING_PACKAGING_PASS / AWAITING_AUDIT_AND_FORMAL_LEGAL_REVIEW**

The exact-source cold Installer build and the corrected warm-cache acceptance run both completed successfully. The unsigned Windows Installer installed and passed its installed capability smoke. Redistribution evidence gates report zero unresolved shipped files, components, notices, or source packages. This is engineering packaging evidence only: `legal_review_required=true`, one external prerequisite remains (formal legal review), and `public_release_authorized=false`. No legal opinion, independent audit pass, public release, or task closure is claimed.

## Source and validation

- Canonical source: `Sekiph82/PackLab`, `main`.
- Implementation source: `452fe8934b0d56011af8c117555dd059d5c63462` (fixes frozen CAD-export commit provenance using validated embedded build provenance).
- Focused test: `uv run pytest tests/core/test_cad_export_manifest.py -q` — 5 passed.
- Exact-SHA Quality run [38646355410](https://github.com/Sekiph82/PackLab/actions/runs/38646355410) passed Ruff lint, Ruff format, mypy, and the full suite: 2,158 passed, 10 skipped, 1 deselected, 2 warnings.
- Cold Installer run [38646432056](https://github.com/Sekiph82/PackLab/actions/runs/38646432056) and corrected warm-cache run [38649528145](https://github.com/Sekiph82/PackLab/actions/runs/38649528145) completed with all jobs successful.
- Both runs restored/authenticated the retained OCCT SDK checkpoint. The warm run restored and fail-closed validated the exact OCP runtime cache, validated it against the same-run OCCT payload, and skipped the OCP source build and cache save. No OCCT or OCP native compilation occurred during these packaging runs.

## Packaged capability and Installer evidence

- Frozen NumPy probe, Open3D-first clean-process probe, and complete offline Studio smoke passed.
- Final compliance evidence records 622 staged files (1,283,197,252 bytes), 622 mapped files, 126 collected notices versus 63 required, zero missing notices/source packages, zero unresolved components/files/items, and zero forbidden Qt components. `engineering_packaging_status=CLEARED_FOR_PL0350_ENGINEERING_PACKAGING`; `legal_review_required=true`; `public_release_authorized=false`.
- The unsigned Installer was 877,587,276 bytes, SHA-256 `8cc6fb20e4b88093a8647a5c5c511ee49db0a33de3c6d2c937c14b6544eb30f2`. The hosted installed smoke reported PASS against the same source revision and Installer digest.
- Installed, network-free capabilities all passed: DXF export, OCP CAD/revolve/bounds/tessellation, Open3D point-cloud conversion, Qt Studio GUI, Qt vector/PDF, and STEP write/read round-trip. Blender, COLMAP, and OpenMVS are listed as external architecture dependencies and are not bundled.
- Cold Installer Actions artifact: ID `11933254991`, 877,242,879 bytes, artifact digest `sha256:10e6a3564e35b9aa5c8a3946d145d8e9ebe61608149978dd7c787fe4ec1dd1c8`. Warm Installer artifact: ID `11935390977`, 877,253,435 bytes, artifact digest `sha256:3e9762e4d3faf6d0363f9714bfbdcb0d0b2d9dc9e73769ebfaac757c9af23e15`. Both runs uploaded only after the installed smoke passed. The verified owner copy is retained locally outside the project checkout; this report does not expose a public binary-download link.
- Warm final text-only compliance artifact: ID `11934773569`, 345,753 bytes, digest `sha256:29a1dc6014de36ec0c2b7db463bc28b7e4a8d6569e915d64b9069834c8260631`. Warm pre-clearance artifact: ID `11934344670`, 339,063 bytes, digest `sha256:df84c88cc71549aba516cac4701ae81f102620cd1efbee73cf8232d81c1c08c6`.

## Compliance and legal boundary

The combined evidence chain covers the exact staged Open3D wheel and native dependencies, Qt/PySide6/Shiboken licensing route and notices, corresponding-source/relinking material, Microsoft runtime provenance, PackLab ownership/provenance notice, and the complete shipped-file inventory. The automated gate now has zero unresolved items and retains the selected LGPLv3 compliance path. Formal legal review is still explicitly required; the engineering gate does not establish a legal entitlement or authorize public redistribution.

The owner decision remains proprietary internal business software for authorized factory employees, without external sales or public source/binary release. Repository metadata was public at the start of this continuation; following the explicit owner decision, repository visibility was changed to private and verified (`private=true`, `visibility=private`). This prevents further public access to source and workflow artifacts, though it cannot recall copies downloaded before the change. The exact-source Installer is unsigned and suitable for controlled internal evaluation/deployment subject to formal legal review and the owner's distribution controls. Root `TASKS.md` is unchanged.

## Previous failures and correction

Run `38642987529` had passed compliance and built the Installer but its installed smoke failed because the frozen app had no Git metadata for the CAD-export manifest. The implementation now obtains the revision from validated frozen `packlab-build-provenance.json` when `PACKLAB_BUILD_REVISION` is absent. Focused tests cover valid, missing, and malformed evidence. Cold run `38646432056` then passed installed smoke; warm run `38649528145` independently passed the same acceptance path and the genuine cache-hit check. The earlier warm dispatch `38649365194` was a downstream-skipped no-op and is not counted as cache acceptance.

## Governance and handoff

Final implementation and evidence are recorded in the append-only [Codex log](PL-0350_ALL_REMAINING_WORK_ONE_SHOT_CODEX_LOG.md). The Desktop owner checkout, existing owner binaries, original assets, and `OwnerDev` were not modified by this continuation. No `TASKS.md`, frozen prompt/criteria, or ChatGPT audit file was edited or created. The builder handoff is **AWAITING_AUDIT**; independent audit and formal legal review remain outstanding.
