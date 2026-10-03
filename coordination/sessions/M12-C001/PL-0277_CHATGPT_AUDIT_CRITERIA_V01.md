# PL-0277 - ChatGPT Audit Criteria V01

Task: **Support importing a reusable trigger/pump library component**

All criteria are mandatory.

1. M12 tracker/master authorization, safe synchronization, M11 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Implement a PackLab-owned reusable trigger/pump component import contract for local library assets. Require explicit component version, source/license/provenance metadata, package geometry/attachment reference contract and integrity digest. Do not download assets automatically, infer license, embed private supplier data or silently accept unreviewed binaries. Imported library geometry is reusable design/reference geometry, never Scan Master/captured evidence.
3. Tests/evidence cover at minimum: valid local component import, digest tamper, missing license/provenance, unsupported version, private/raw-path rejection, deterministic identity, no network download, authority=library design component.
4. Scan Master/Design Model/assembly/library/flexible-pack authority boundaries and inherited scale/deferred-validation state remain explicit; no hidden physical/manufacturing truth is invented.
5. No unreviewed CAD/backend/dependency/private/unlicensed asset/later-child or M13+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0277_CODEX_PROMPT_V01.md
