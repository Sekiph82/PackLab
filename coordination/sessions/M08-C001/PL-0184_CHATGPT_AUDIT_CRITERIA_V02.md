# PL-0184 - ChatGPT Audit Criteria V02

Task: **Remediate immutable segmentation-contract serialization and digest integrity**

Source audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0184_CHATGPT_AUDIT_V02.md  
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0184_CODEX_PROMPT_V02.md

All criteria are mandatory.

1. The live tracker authorizes the M08-C001 remediation batch and PL-0184 V02
   in order; PL-0185+ and M09 remain unauthorized until the remediation
   frontier is independently closed.
2. The actual diff fixes the V01 integrity finding by making nested prompt data
   immutable or equivalently mutation-safe while preserving the public JSON
   serialization shape and deterministic contract behavior.
3. Public tests prove caller-owned and exposed nested mappings/sequences cannot
   change serialized prompt, mask-artifact, or mask-revision content or leave a
   stale digest; prior V01 success, failure, coordinate, provenance, path and
   source-immutability behavior remains green.
4. RAW_CAPTURE/source bytes, prior accepted authority contracts, revision
   identity and workspace/provenance boundaries remain intact.
5. No model/runtime/dependency, private data, generated unsafe output, UI-owned
   domain truth, native/physical claim or later-child/later-milestone scope is
   included.
6. Required focused/full/static/security/scope/remote checks and the V02 log
   are complete and truthful; the log ends exactly with
   `READY_FOR_INDEPENDENT_AUDIT`.

Closure requires a fresh independent audit; this remediation does not accept
PL-0185 or any later child by itself.
