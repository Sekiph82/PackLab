# PL-0350 | Owner Deployment and AI-Originated Work Rights Decision

Recorded: 2026-10-14
Scope: PackLab, M16-C001, PL-0350 only. This document is an **owner-supplied deployment-intent record plus a technical rights interpretation**, not a signed legal transfer or certificate of copyright title.

## Owner deployment facts (declared in conversation)

1. PackLab is being developed **for the owner's own factory operations**.
2. It currently runs on the owner's computer.
3. Approximately two months from now, the owner plans to operate PackLab on **multiple computers at the Kenya factory** for authorized factory personnel.
4. The owner explicitly states that the software **will not be sold to outside customers**.
5. The owner reports that PackLab's original project code and custom visuals were generated at their direction by ChatGPT/Codex, and delegates the preferred project licensing/deployment policy decision to ChatGPT.

These are the actual user-declared facts. The precise incorporated legal entities, employment/IP assignments, any separately supplied reference graphics and third-party source contributions **have not been legally verified**.

## Decision: proprietary controlled INTERNAL BUSINESS software, not personal-only

- **Classification:** `PROPRIETARY_INTERNAL_BUSINESS_USE` / `MULTI_WORKSTATION_KENYA_FACTORY`.
- Initial target: owner's controlled Windows computer. Subsequent target: managed Windows workstations accessible only to the owner's factory business and authorized staff in Kenya. Internal operational use is permitted as the **intended functional product scope**, not a retail/commercial customer release.
- The contemplated deployment has **more than one computer**, so do not label the product `PERSONAL_USE_ONLY` and do not build machine-locked single-PC licensing based on the historical personal test.
- `third_party_customer_sales=false`, `public_binary_release_authorized=false`, `public_source_license_granted=false` and `external_distribution_marketing=false`.
- Internal business use is commercial **in purpose**, even if the application is not sold; do not misclassify it as noncommercial/personal for third-party license compliance.
- Do not open-source PackLab's proprietary project-originated code or artwork, publish GitHub Release installers, sign as a commercial release, or invent a company/rights-holder name without separate authorization. A repository being readable on GitHub does not itself establish a right for others to redistribute proprietary material.

## AI-originated code and art: who controls it?

For content output under ChatGPT's applicable consumer terms, **as between the user and OpenAI, to the extent permitted by law, the user owns the Output and OpenAI assigns any rights it has**. This is NOT a warranty that all generated material is unique or free of third-party claims, nor proof of title to material contributed through separate tools or referenced external assets.

Authoritative primary source:
https://openai.com/policies/terms-of-use/ (section: Content, Ownership of content, Similarity of content).
If the work was actually performed under OpenAI business/developer terms, compare:
https://openai.com/policies/services-agreement/ (section 4.1).

**Project policy chosen:** treat demonstrably original PackLab code, design direction and custom AI-generated assets as **user-controlled/proprietary project output**, for internal factory use across managed company workstations, subject to provenance audit and applicable law. The AI assistant does **not** claim ownership, attach a personal royalty, insist on an open-source PackLab license, or grant rights it does not hold. The project owner's personal name is not asserted here as a formal corporate copyright registration or deed of assignment.

Any code/assets imported from GitHub, open-source projects, third-party photographs/icons/reference materials or commercial packages retain their respective upstream licenses/attribution obligations. A business legal entity in Kenya may be distinct from the owner's legal entity; actual inter-entity distribution arrangements should be reviewed before transfer to a separate legal person. This does **not** preclude engineering the internal multi-PC deployment, but does not assert an unverified corporate assignment.

## Third-party license route chosen for engineering

- **Qt for Python / PySide6 / Shiboken:** proceed with a *provisional, source-backed LGPLv3/open-source compliance plan*, rather than presuming an unpurchased Qt commercial license. Verify exact modules/components, GPL-only exclusions, all license/NOTICE/source/replacement/relinking requirements applicable to the actual frozen Installer, and any obligations triggered by conveyance to a distinct legal entity. If the concrete package cannot satisfy the open-source path, STOP for the true license choice. This decision is **not** an LGPL clearance claim.
- **Open3D:** verify its v0.20.0 MIT LICENSE for core plus the **exact distributed wheel's** bundled third-party source, license and NOTICE inventory. Do not treat the top-level MIT file as clearing all transitives.
- **NumPy hashed MSVC DLL:** no blanket exemption. Prove exact bytes/owner/app-local Microsoft REDIST entitlement, or implement a source-backed packaging alternative without bundling the unowned copy that passes fresh-Windows frozen smoke.
- **OCCT/OCP/fmt/Qt dependencies:** retain byte-level source/lock evidence and independent license notices. No unsupported permission waivers.

Primary vendor references:
https://doc.qt.io/qtforpython-6/
https://github.com/isl-org/Open3D/blob/v0.20.0/LICENSE
https://github.com/isl-org/Open3D/blob/v0.20.0/3rdparty/README.md
https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute
https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files

## Effect on PL-0350

- **Resolve the former owner-intent ambiguity.** There is no need to re-ask `A: personal PC vs B: sell product`: the correct answer is proprietary **factory-internal multi-PC commercial-operation use**, no customer sales/public release.
- The project-originated rights policy no longer requires a different owner reply just because ChatGPT/Codex generated source/visuals. Codex must verify which exact files are truly project-originated and identify exceptions instead of requiring an impossible blanket copyright certificate from the user.
- Do **not** label `component:packlab` fully cleared until the compliance evidence pipeline maps original files versus third-party contributions and records this decision. The remaining Qt/Open3D/MSVC/NOTICE/source obligations stay **BLOCKED until independently verified**. No installer release may bypass a failed file-level redistribution gate.
- **Priority:** preserve the validated OCP runtime and text-only compliance artifacts before short-lived artifact expiry (**2026-10-15 19:09–19:12 UTC** for the latest run). Preserve without OCCT/OCP recompile. Older recovered OCCT SDK artifact 11796717315 has longer retention through **2026-10-27 07:59:40 UTC**.
- Codex continues under the EXISTING **single** `PL-0350_ALL_REMAINING_WORK_ONE_SHOT_MASTER_CODEX_PROMPT.md` to gather technical third-party evidence and implement one compliant unsigned internal multi-workstation Installer when engineering gates actually clear. **No new R07/R08 prompt** or public release.
- PL-0351 separate clean-target installation and rollout acceptance, M17 and PL-0368 remain outside this task.

**Audit status:** This is a precise deployment/rights INTENT decision, not counsel-certified distribution clearance. Keep `legal_review_required=true` and `public_release_authorized=false` at all times. Do not substitute this document for exact LGPL/Microsoft/third-party obligations or transfer rights between distinct legal entities.
