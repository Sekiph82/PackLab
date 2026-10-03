# PL-0281 - ChatGPT Audit Criteria V01

Task: **Allow swapping trigger/pump variants without modifying bottle geometry**

All criteria are mandatory.

1. M12 tracker/master authorization, safe synchronization, M11 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Implement explicit trigger/pump variant replacement in the assembly graph. Swap must create a new assembly revision, preserve bottle/body and Scan Master parents byte-for-byte, validate attachment compatibility and leave previous assembly history intact. Incompatible variants fail closed; no silent bottle adaptation.
3. Tests/evidence cover at minimum: compatible swap, incompatible attachment, stale variant, body revision unchanged, old assembly retained, deterministic new revision, undo/redo/history compatibility.
4. Scan Master/Design Model/assembly/library/flexible-pack authority boundaries and inherited scale/deferred-validation state remain explicit; no hidden physical/manufacturing truth is invented.
5. No unreviewed CAD/backend/dependency/private/unlicensed asset/later-child or M13+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0281_CODEX_PROMPT_V01.md
